/**
 * LLM-based SLA Extraction Service
 * 
 * Uses Amazon Nova 2 Lite via OpenRouter API to extract structured
 * SLA details from car lease documents (both images and text).
 */

import {
  SLA_EXTRACTION_SYSTEM_PROMPT,
  SLA_IMAGE_USER_PROMPT,
  SLA_TEXT_USER_PROMPT,
  EMPTY_SLA_TEMPLATE,
} from './slaPrompt';

// ─── Configuration ───────────────────────────────────────────────
const OPENROUTER_API_URL = 'https://openrouter.ai/api/v1/chat/completions';
const API_KEY = import.meta.env.VITE_OPENROUTER_API_KEY;
const MODEL = 'amazon/nova-lite-v1';

if (!API_KEY) {
  console.error('Missing VITE_OPENROUTER_API_KEY in .env file. Create a .env file in the project root with your key.');
}

// ─── Core LLM Extraction ────────────────────────────────────────

/**
 * Extract SLA details from a document image (base64-encoded).
 * Sends the image to Amazon Nova 2 Lite via OpenRouter for analysis.
 */
export async function extractSLAFromImage(base64Image) {
  const response = await fetch(OPENROUTER_API_URL, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${API_KEY}`,
      'HTTP-Referer': window.location.origin,
      'X-Title': 'Car Lease Analyzer',
    },
    body: JSON.stringify({
      model: MODEL,
      messages: [
        {
          role: 'system',
          content: SLA_EXTRACTION_SYSTEM_PROMPT,
        },
        {
          role: 'user',
          content: [
            { type: 'text', text: SLA_IMAGE_USER_PROMPT },
            {
              type: 'image_url',
              image_url: { url: base64Image },
            },
          ],
        },
      ],
      temperature: 0.1,
      max_tokens: 4096,
    }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(
      errorData.error?.message || `API Error: ${response.status} ${response.statusText}`
    );
  }

  const data = await response.json();
  const content = data.choices?.[0]?.message?.content || '';
  return parseJSONResponse(content);
}

/**
 * Extract SLA details from plain text of a lease document.
 * Used for text-based extraction or as a fallback when vision fails.
 */
export async function extractSLAFromText(text) {
  const response = await fetch(OPENROUTER_API_URL, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${API_KEY}`,
      'HTTP-Referer': window.location.origin,
      'X-Title': 'Car Lease Analyzer',
    },
    body: JSON.stringify({
      model: MODEL,
      messages: [
        {
          role: 'system',
          content: SLA_EXTRACTION_SYSTEM_PROMPT,
        },
        {
          role: 'user',
          content: SLA_TEXT_USER_PROMPT(text),
        },
      ],
      temperature: 0.1,
      max_tokens: 4096,
    }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(
      errorData.error?.message || `API Error: ${response.status} ${response.statusText}`
    );
  }

  const data = await response.json();
  const content = data.choices?.[0]?.message?.content || '';
  return parseJSONResponse(content);
}

// ─── JSON Parsing ────────────────────────────────────────────────

/**
 * Parse JSON from LLM response, handling various response formats
 * (raw JSON, markdown code blocks, mixed text + JSON).
 */
function parseJSONResponse(content) {
  // 1. Try direct parse
  try {
    return validateAndMerge(JSON.parse(content));
  } catch {
    // continue
  }

  // 2. Try extracting from markdown code block
  const codeBlockMatch = content.match(/```(?:json)?\s*([\s\S]*?)```/);
  if (codeBlockMatch) {
    try {
      return validateAndMerge(JSON.parse(codeBlockMatch[1].trim()));
    } catch {
      // continue
    }
  }

  // 3. Try extracting first JSON object
  const braceMatch = content.match(/\{[\s\S]*\}/);
  if (braceMatch) {
    try {
      return validateAndMerge(JSON.parse(braceMatch[0]));
    } catch {
      // continue
    }
  }

  throw new Error(
    'Failed to parse structured SLA data from LLM response. Raw output:\n' + content
  );
}

/**
 * Merge extracted data with the empty template to ensure all fields exist.
 */
function validateAndMerge(extracted) {
  const merged = JSON.parse(JSON.stringify(EMPTY_SLA_TEMPLATE));

  for (const section of Object.keys(merged)) {
    if (section === 'additional_terms') {
      if (Array.isArray(extracted.additional_terms)) {
        merged.additional_terms = extracted.additional_terms;
      }
      continue;
    }

    if (typeof merged[section] === 'object' && extracted[section]) {
      for (const key of Object.keys(merged[section])) {
        if (typeof merged[section][key] === 'object' && extracted[section][key]) {
          // Nested object (e.g., parties.lessor)
          for (const subKey of Object.keys(merged[section][key])) {
            if (extracted[section][key][subKey] !== undefined && extracted[section][key][subKey] !== '') {
              merged[section][key][subKey] = extracted[section][key][subKey];
            }
          }
        } else if (extracted[section][key] !== undefined && extracted[section][key] !== '') {
          merged[section][key] = extracted[section][key];
        }
      }
    }
  }

  return merged;
}

// ─── Local Database (localStorage) + Backend Sync ───────────────

import { createContract, createSLA, getContracts, getSLAs, deleteContract, deleteSLA } from './apiService.js';

const DB_KEY = 'car_lease_sla_database';

export async function saveSLARecord(record) {
  // Save to localStorage as local cache
  const records = getSLARecordsLocal();
  const newRecord = {
    id: Date.now().toString(),
    timestamp: new Date().toISOString(),
    fileName: record.fileName,
    slaData: record.slaData,
    extractionMethod: record.extractionMethod || 'image',
  };

  // Persist to MongoDB backend (duplicate check happens server-side)
  try {
    const contract = await createContract({
      file_name: record.fileName,
      extracted_text: record.extractedText || '',
      status: 'extracted',
    });
    if (contract._id) {
      const slaPayload = {
        contract_id: contract._id,
        raw_sla_json: record.slaData,
        monthly_payment: record.slaData?.lease_terms?.monthly_payment || '',
        down_payment: record.slaData?.lease_terms?.down_payment || '',
        residual_value: record.slaData?.end_of_lease_options?.residual_value || '',
        mileage_limit: record.slaData?.mileage_terms?.annual_mileage_limit || '',
        overage_fee: record.slaData?.mileage_terms?.excess_mileage_charge_per_mile || '',
        early_termination_fee: record.slaData?.penalties?.early_termination_fee || '',
        maintenance_responsibility: record.slaData?.sla_obligations?.maintenance_responsibility || '',
        insurance_requirement: record.slaData?.sla_obligations?.insurance_requirements || '',
      };
      await createSLA(slaPayload);
      newRecord.contractId = contract._id;
    }
  } catch (err) {
    if (err.code === 'DUPLICATE') {
      throw err; // Re-throw duplicate errors so the UI can handle them
    }
    console.warn('Backend save failed (data is still in localStorage):', err.message);
  }

  // Only save to localStorage if backend succeeded (no duplicate)
  records.push(newRecord);
  localStorage.setItem(DB_KEY, JSON.stringify(records));

  return newRecord;
}

function getSLARecordsLocal() {
  try {
    const data = localStorage.getItem(DB_KEY);
    return data ? JSON.parse(data) : [];
  } catch {
    return [];
  }
}

export function getSLARecords() {
  return getSLARecordsLocal();
}

export function deleteSLARecord(id) {
  const records = getSLARecordsLocal().filter((r) => r.id !== id);
  localStorage.setItem(DB_KEY, JSON.stringify(records));
  return records;
}

export function clearSLADatabase() {
  localStorage.removeItem(DB_KEY);
}

// ─── Negotiation Chatbot ─────────────────────────────────────────

const NEGOTIATION_SYSTEM_PROMPT = `You are an expert car lease negotiation advisor. Help users understand and negotiate their lease contracts.

RESPONSE RULES — follow these strictly:
1. Be concise. Max 3-4 short paragraphs per answer. No filler, no disclaimers, no "certainly" or "great question".
2. Use simple markdown: **bold** for key terms/numbers, bullet points for lists. Never use ### headers or long horizontal rules.
3. When lease data is loaded, reference the user's ACTUAL numbers (e.g. "$350/mo", "12,000 mi/yr") — don't give generic advice.
4. Give actionable advice — what to say, what number to counter with, what to ask the dealer.
5. If the user asks a yes/no question, answer yes or no first, then explain briefly.
6. Never repeat the full contract data back. Only mention the specific terms relevant to the question.
7. Keep bullet lists to 3-5 items max. No walls of text.`;

/**
 * Send a conversation to the negotiation chatbot and return the assistant reply.
 * @param {Array<{role: string, content: string}>} messages - Full conversation history
 * @param {Object|null} slaContext - Optional extracted SLA data to include as context
 */
export async function chatWithNegotiationBot(messages, slaContext = null) {
  // Build a compact context string instead of dumping the full JSON
  let systemContent = NEGOTIATION_SYSTEM_PROMPT;
  if (slaContext) {
    const s = slaContext;
    const summary = [
      s.vehicle_details?.year && `Vehicle: ${s.vehicle_details.year} ${s.vehicle_details.make || ''} ${s.vehicle_details.model || ''}`.trim(),
      s.lease_terms?.monthly_payment && `Monthly Payment: ${s.lease_terms.monthly_payment}`,
      s.lease_terms?.down_payment && `Down Payment: ${s.lease_terms.down_payment}`,
      s.lease_terms?.duration_months && `Term: ${s.lease_terms.duration_months} months`,
      s.lease_terms?.total_lease_cost && `Total Cost: ${s.lease_terms.total_lease_cost}`,
      s.mileage_terms?.annual_mileage_limit && `Mileage Limit: ${s.mileage_terms.annual_mileage_limit}/yr`,
      s.mileage_terms?.excess_mileage_charge_per_mile && `Excess Mileage Fee: ${s.mileage_terms.excess_mileage_charge_per_mile}`,
      s.penalties?.early_termination_fee && `Early Termination: ${s.penalties.early_termination_fee}`,
      s.penalties?.late_payment_fee && `Late Fee: ${s.penalties.late_payment_fee}`,
      s.end_of_lease_options?.residual_value && `Residual Value: ${s.end_of_lease_options.residual_value}`,
      s.end_of_lease_options?.purchase_option && `Purchase Option: ${s.end_of_lease_options.purchase_option}`,
      s.sla_obligations?.maintenance_responsibility && `Maintenance: ${s.sla_obligations.maintenance_responsibility}`,
      s.sla_obligations?.insurance_requirements && `Insurance: ${s.sla_obligations.insurance_requirements}`,
      s.lease_terms?.security_deposit && `Security Deposit: ${s.lease_terms.security_deposit}`,
    ].filter(Boolean).join('\n');
    if (summary) {
      systemContent += `\n\nUser's lease details:\n${summary}`;
    }
  }

  const response = await fetch(OPENROUTER_API_URL, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${API_KEY}`,
      'HTTP-Referer': window.location.origin,
      'X-Title': 'Car Lease Negotiation Bot',
    },
    body: JSON.stringify({
      model: MODEL,
      messages: [
        { role: 'system', content: systemContent },
        ...messages,
      ],
      temperature: 0.5,
      max_tokens: 512,
    }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(
      errorData.error?.message || `API Error: ${response.status} ${response.statusText}`
    );
  }

  const data = await response.json();
  return data.choices?.[0]?.message?.content || '';
}
