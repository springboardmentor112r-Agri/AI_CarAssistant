import { useState, useEffect, useRef } from 'react';
import * as pdfjsLib from 'pdfjs-dist';
import pdfjsWorker from 'pdfjs-dist/build/pdf.worker.min.mjs?url';
import {
  extractSLAFromImage,
  extractSLAFromText,
  saveSLARecord,
  getSLARecords,
  deleteSLARecord,
  clearSLADatabase,
  chatWithNegotiationBot,
} from './services/llmService';
import AuthPage from './components/AuthPage';
import ChatMarkdown from './components/ChatMarkdown';
import spCarSvg from './assets/sp-car.svg';
import { upsertVehicle, addMessage, createThread, getSLAsWithContracts, getMarketPrices } from './services/apiService';
import { analyzeContract, buildMarketComparison, calculateMarketScore } from './services/fairnessScoring';
import ContractGraphs from './components/ContractGraphs';
import './App.css';

pdfjsLib.GlobalWorkerOptions.workerSrc = pdfjsWorker;

// ─── Section Label Map ───────────────────────────────────────────
const SECTION_LABELS = {
  document_info: 'Document Information',
  parties: 'Parties',
  vehicle_details: 'Vehicle Details',
  lease_terms: 'Lease Terms',
  mileage_terms: 'Mileage Terms',
  sla_obligations: 'SLA Obligations',
  penalties: 'Penalties',
  end_of_lease_options: 'End of Lease Options',
  additional_terms: 'Additional Terms',
};

const SUGGESTED_PROMPTS = [
  'What lease terms are typically negotiable?',
  'Explain my monthly payment and what affects it',
  'How can I reduce excess mileage penalties?',
  'What should I watch out for before signing?',
  'Help me understand my end-of-lease options',
];

const FIELD_LABELS = {
  document_type: 'Document Type',
  document_date: 'Document Date',
  contract_number: 'Contract Number',
  lessor: 'Lessor',
  lessee: 'Lessee',
  name: 'Name',
  address: 'Address',
  contact: 'Contact',
  license_number: 'License Number',
  make: 'Make',
  model: 'Model',
  year: 'Year',
  vin: 'VIN',
  color: 'Color',
  mileage_at_start: 'Starting Mileage',
  start_date: 'Start Date',
  end_date: 'End Date',
  duration_months: 'Duration (Months)',
  monthly_payment: 'Monthly Payment',
  down_payment: 'Down Payment',
  security_deposit: 'Security Deposit',
  total_lease_cost: 'Total Lease Cost',
  annual_mileage_limit: 'Annual Mileage Limit',
  total_mileage_limit: 'Total Mileage Limit',
  excess_mileage_charge_per_mile: 'Excess Mileage Charge',
  maintenance_responsibility: 'Maintenance',
  insurance_requirements: 'Insurance Requirements',
  wear_and_tear_policy: 'Wear & Tear Policy',
  service_schedule: 'Service Schedule',
  late_payment_fee: 'Late Payment Fee',
  early_termination_fee: 'Early Termination Fee',
  excess_wear_charges: 'Excess Wear Charges',
  missing_equipment_charges: 'Missing Equipment Charges',
  purchase_option: 'Purchase Option',
  residual_value: 'Residual Value',
  return_conditions: 'Return Conditions',
};

function App() {
  // ─── Auth State ────────────────────────────────────────────────
  const [currentUser, setCurrentUser] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem('sla_session') || 'null');
    } catch {
      return null;
    }
  });

  const handleAuthSuccess = (user) => setCurrentUser(user);

  const handleLogout = () => {
    localStorage.removeItem('sla_session');
    localStorage.removeItem('sla_token');
    setCurrentUser(null);
  };

  // ─── State ─────────────────────────────────────────────────────
  const [activeTab, setActiveTab] = useState('extract');
  const [selectedFile, setSelectedFile] = useState(null);
  const [base64Image, setBase64Image] = useState(null);
  const [imagePreview, setImagePreview] = useState('');
  const [slaResult, setSlaResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [isDragOver, setIsDragOver] = useState(false);
  const [statusMessage, setStatusMessage] = useState('');
  const [records, setRecords] = useState([]);
  const [selectedRecord, setSelectedRecord] = useState(null);
  const [jsonViewMode, setJsonViewMode] = useState('table');
  const [dbViewMode, setDbViewMode] = useState('table');
  const [pdfExtractedText, setPdfExtractedText] = useState('');
  const fileInputRef = useRef(null);

  // ─── VIN State ─────────────────────────────────────────────────
  const [vinInput, setVinInput] = useState('');
  const [vinReport, setVinReport] = useState(null);
  const [vinLoading, setVinLoading] = useState(false);
  const [vinError, setVinError] = useState('');

  // ─── Chatbot State ─────────────────────────────────────────────
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const chatEndRef = useRef(null);

  // ─── Market Price State ────────────────────────────────────────
  const [marketData, setMarketData] = useState(null);
  const [marketLoading, setMarketLoading] = useState(false);

  // ─── Compare State ─────────────────────────────────────────────
  const [compareSelected, setCompareSelected] = useState([]);
  const [showComparison, setShowComparison] = useState(false);
  const [compareRecords, setCompareRecords] = useState([]);
  const [compareLoading, setCompareLoading] = useState(false);

  const fetchCompareRecords = async () => {
    setCompareLoading(true);
    try {
      const data = await getSLAsWithContracts();
      setCompareRecords(Array.isArray(data) ? data : []);
    } catch (err) {
      console.warn('Failed to fetch contracts from MongoDB:', err.message);
      setCompareRecords([]);
    } finally {
      setCompareLoading(false);
    }
  };

  useEffect(() => {
    setRecords(getSLARecords());
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages]);

  // ─── File Handling ─────────────────────────────────────────────
  const handleFileSelect = async (file) => {
    if (!file) return;
    const isImage = file.type.startsWith('image/');
    const isPDF = file.type === 'application/pdf';
    if (!isImage && !isPDF) {
      setError('Please select a valid image or PDF file');
      return;
    }
    if (file.size > 20 * 1024 * 1024) {
      setError('File size must be less than 20 MB');
      return;
    }
    setSelectedFile(file);
    setError('');
    setSlaResult(null);
    setStatusMessage('');

    if (isPDF) {
      await handlePDFFile(file);
    } else {
      handleImageFile(file);
    }
  };

  const handleImageFile = (file) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      setImagePreview(e.target.result);
      setBase64Image(e.target.result);
    };
    reader.readAsDataURL(file);
  };

  const handlePDFFile = async (file) => {
    try {
      setIsLoading(true);
      setStatusMessage('Processing PDF…');
      const arrayBuffer = await file.arrayBuffer();
      const loadingTask = pdfjsLib.getDocument({ data: arrayBuffer });
      const pdf = await loadingTask.promise;
      const totalPages = pdf.numPages;

      // 1️⃣  Try text extraction from ALL pages first (cheaper & more accurate)
      let fullText = '';
      for (let p = 1; p <= totalPages; p++) {
        setStatusMessage(`Extracting text from page ${p} of ${totalPages}…`);
        const page = await pdf.getPage(p);
        const textContent = await page.getTextContent();
        const pageText = textContent.items.map((item) => item.str).join(' ');
        fullText += `--- Page ${p} ---\n${pageText}\n\n`;
      }

      // 2️⃣  Render first page for preview
      const firstPage = await pdf.getPage(1);
      const previewScale = 2.0;
      const previewVp = firstPage.getViewport({ scale: previewScale });
      const previewCanvas = document.createElement('canvas');
      previewCanvas.width = previewVp.width;
      previewCanvas.height = previewVp.height;
      const previewCtx = previewCanvas.getContext('2d');
      await firstPage.render({ canvasContext: previewCtx, viewport: previewVp }).promise;
      const previewDataUrl = previewCanvas.toDataURL('image/jpeg', 0.95);
      setImagePreview(previewDataUrl);

      // 3️⃣  Decide extraction path
      if (fullText.trim().length > 200) {
        // Enough text → use text-based extraction (no vision model needed)
        setBase64Image(null);
        // Store extracted text so handleExtract can use it
        setPdfExtractedText(fullText);
        setStatusMessage(`Extracted text from ${totalPages} page(s). Ready to analyse.`);
      } else {
        // Scanned / image-only PDF → stitch page images (up to 5 pages for API limits)
        const maxImagePages = Math.min(totalPages, 5);
        const pageCanvases = [];
        for (let p = 1; p <= maxImagePages; p++) {
          setStatusMessage(`Rendering page ${p} of ${maxImagePages} as image…`);
          const page = await pdf.getPage(p);
          const vp = page.getViewport({ scale: 1.5 });
          const c = document.createElement('canvas');
          c.width = vp.width;
          c.height = vp.height;
          await page.render({ canvasContext: c.getContext('2d'), viewport: vp }).promise;
          pageCanvases.push(c);
        }
        // Stitch into one tall image
        const totalH = pageCanvases.reduce((s, c) => s + c.height, 0);
        const maxW = Math.max(...pageCanvases.map((c) => c.width));
        const combined = document.createElement('canvas');
        combined.width = maxW;
        combined.height = totalH;
        const cctx = combined.getContext('2d');
        let yOff = 0;
        for (const pc of pageCanvases) {
          cctx.drawImage(pc, 0, yOff);
          yOff += pc.height;
        }
        const combinedUrl = combined.toDataURL('image/jpeg', 0.9);
        setBase64Image(combinedUrl);
        setPdfExtractedText('');
        setStatusMessage(`Rendered ${maxImagePages} page(s) as image. Ready to analyse.`);
      }
    } catch (err) {
      console.error('PDF processing error:', err);
      // Fallback: read the PDF as a generic image data URL so user can still try
      try {
        const reader = new FileReader();
        reader.onload = (e) => {
          setBase64Image(e.target.result);
          setImagePreview('');
          setError('PDF preview unavailable, but you can still attempt extraction.');
        };
        reader.readAsDataURL(file);
      } catch {
        setError(`Failed to process PDF: ${err.message}. Please try an image file instead.`);
        setSelectedFile(null);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleRemoveFile = () => {
    setSelectedFile(null);
    setBase64Image(null);
    setImagePreview('');
    setPdfExtractedText('');
    setSlaResult(null);
    setMarketData(null);
    setError('');
    setStatusMessage('');
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  // ─── SLA Extraction ───────────────────────────────────────────
  const handleExtract = async () => {
    if (!base64Image && !pdfExtractedText) {
      setError('Please upload a document first');
      return;
    }

    setIsLoading(true);
    setError('');
    setSlaResult(null);
    setStatusMessage('');

    const useText = pdfExtractedText && pdfExtractedText.trim().length > 200;

    try {
      const data = useText
        ? await extractSLAFromText(pdfExtractedText)
        : await extractSLAFromImage(base64Image);
      setSlaResult(data);

      // Fetch market prices for the extracted vehicle
      const vd = data.vehicle_details || {};
      if (vd.make && vd.model && vd.year &&
          vd.make !== 'Not specified' && vd.model !== 'Not specified' && vd.year !== 'Not specified') {
        setMarketLoading(true);
        getMarketPrices(vd.make, vd.model, vd.year)
          .then(md => setMarketData(md))
          .catch(() => setMarketData(null))
          .finally(() => setMarketLoading(false));
      }

      const record = await saveSLARecord({
        fileName: selectedFile?.name || 'uploaded-document',
        slaData: data,
        extractionMethod: useText ? 'text' : 'image',
        extractedText: useText ? pdfExtractedText : '',
      });
      setRecords(getSLARecords());
      setStatusMessage('SLA extraction complete!');
    } catch (err) {
      if (err.code === 'DUPLICATE') {
        setError('This contract has already been uploaded. Please upload a different document.');
      } else {
        console.error('Extraction error:', err);
        setError(`Extraction failed: ${err.message}`);
      }
    } finally {
      setIsLoading(false);
    }
  };

  // ─── Database ──────────────────────────────────────────────────
  const handleDeleteRecord = (id) => {
    deleteSLARecord(id);
    setRecords(getSLARecords());
    if (selectedRecord?.id === id) setSelectedRecord(null);
  };

  const handleClearDB = () => {
    if (window.confirm('Delete all SLA records? This cannot be undone.')) {
      clearSLADatabase();
      setRecords([]);
      setSelectedRecord(null);
    }
  };

  const handleExportJSON = (data, fileName) => {
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = fileName;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  // ─── VIN Lookup ───────────────────────────────────────────────
  const handleVinLookup = async () => {
    const vin = vinInput.trim().toUpperCase();
    if (vin.length !== 17) {
      setVinError('VIN must be exactly 17 characters.');
      return;
    }
    setVinLoading(true);
    setVinError('');
    setVinReport(null);
    try {
      // NHTSA Decode VIN
      const decodeRes = await fetch(
        `https://vpic.nhtsa.dot.gov/api/vehicles/decodevin/${vin}?format=json`
      );
      const decodeJson = await decodeRes.json();
      const usefulFields = [
        'Make', 'Model', 'Model Year', 'Vehicle Type', 'Body Class',
        'Engine Number of Cylinders', 'Displacement (L)', 'Fuel Type - Primary',
        'Transmission Style', 'Drive Type', 'Manufacturer Name',
        'Plant Country', 'Number of Seats', 'GVWR',
      ];
      const vehicleDetails = {};
      (decodeJson.Results || []).forEach((item) => {
        if (usefulFields.includes(item.Variable) && item.Value && item.Value !== 'Not Applicable') {
          vehicleDetails[item.Variable] = item.Value;
        }
      });

      // NHTSA Recalls by VIN
      const recallRes = await fetch(
        `https://api.nhtsa.gov/recalls/recallsByVehicle?vin=${vin}`
      );
      const recallJson = await recallRes.json();
      const recalls = recallJson.results || [];

      setVinReport({ vin, vehicleDetails, recalls });

      // Persist to MongoDB
      try {
        await upsertVehicle({
          vin_number: vin,
          make: vehicleDetails['Make'] || '',
          model: vehicleDetails['Model'] || '',
          year: vehicleDetails['Model Year'] || '',
          engine: `${vehicleDetails['Engine Number of Cylinders'] || ''} cyl ${vehicleDetails['Displacement (L)'] || ''}L`.trim(),
          fuel_type: vehicleDetails['Fuel Type - Primary'] || '',
          transmission: vehicleDetails['Transmission Style'] || '',
          recall_history: recalls,
        });
      } catch (dbErr) {
        console.warn('Failed to save VIN to database:', dbErr.message);
      }
    } catch (err) {
      setVinError('Failed to fetch VIN data. Please check your connection and try again.');
    } finally {
      setVinLoading(false);
    }
  };

  // ─── Negotiation Chatbot ──────────────────────────────────────
  const [chatThreadId, setChatThreadId] = useState(null);

  const handleChatSend = async (text) => {
    const userText = (text !== undefined ? text : chatInput).trim();
    if (!userText || chatLoading) return;

    const userMsg = { role: 'user', content: userText };
    const updatedMessages = [...chatMessages, userMsg];
    setChatMessages(updatedMessages);
    setChatInput('');
    setChatLoading(true);

    try {
      const slaContext = slaResult ?? selectedRecord?.slaData ?? null;
      const reply = await chatWithNegotiationBot(updatedMessages, slaContext);
      setChatMessages((prev) => [...prev, { role: 'assistant', content: reply }]);

      // Persist messages to MongoDB
      try {
        let threadId = chatThreadId;
        if (!threadId) {
          // Create a new thread (attach contract if available)
          const contractId = selectedRecord?.contractId || null;
          const threadPayload = contractId ? { contract_id: contractId } : {};
          const thread = await createThread(threadPayload);
          threadId = thread._id;
          setChatThreadId(threadId);
        }
        if (threadId) {
          await addMessage({ thread_id: threadId, sender: 'user', message_text: userText });
          await addMessage({ thread_id: threadId, sender: 'assistant', message_text: reply });
        }
      } catch (dbErr) {
        console.warn('Failed to save chat to database:', dbErr.message);
      }
    } catch (err) {
      setChatMessages((prev) => [
        ...prev,
        { role: 'assistant', content: `Sorry, I encountered an error: ${err.message}` },
      ]);
    } finally {
      setChatLoading(false);
    }
  };

  // ─── Helpers ───────────────────────────────────────────────────
  function findValueInSLA(sla, key) {
    const map = {
      contract_number: sla?.document_info?.contract_number,
      lessee_name: sla?.parties?.lessee?.name,
      lessor_name: sla?.parties?.lessor?.name,
      vehicle: `${sla?.vehicle_details?.year || ''} ${sla?.vehicle_details?.make || ''} ${sla?.vehicle_details?.model || ''}`.trim(),
      vin: sla?.vehicle_details?.vin,
      monthly_payment: sla?.lease_terms?.monthly_payment,
      duration: sla?.lease_terms?.duration_months,
      annual_mileage: sla?.mileage_terms?.annual_mileage_limit,
      excess_mileage: sla?.mileage_terms?.excess_mileage_charge_per_mile,
      late_fee: sla?.penalties?.late_payment_fee,
      early_termination: sla?.penalties?.early_termination_fee,
      residual_value: sla?.end_of_lease_options?.residual_value,
    };
    return map[key] ?? null;
  }

  // ─── Render Helpers ────────────────────────────────────────────
  const renderSLATable = (slaData) => {
    if (!slaData) return null;

    return (
      <div className="sla-table-view">
        {Object.entries(slaData).map(([section, value]) => {
          if (section === 'additional_terms') {
            return (
              <div key={section} className="sla-section">
                <h4 className="sla-section-title">{SECTION_LABELS[section] || section}</h4>
                {Array.isArray(value) && value.length > 0 ? (
                  <ul className="additional-terms-list">
                    {value.map((term, i) => (
                      <li key={i}>{term}</li>
                    ))}
                  </ul>
                ) : (
                  <p className="no-data">No additional terms</p>
                )}
              </div>
            );
          }

          if (typeof value !== 'object') return null;

          const hasNestedObjects = Object.values(value).some(
            (v) => typeof v === 'object' && v !== null
          );

          return (
            <div key={section} className="sla-section">
              <h4 className="sla-section-title">{SECTION_LABELS[section] || section}</h4>
              {hasNestedObjects
                ? Object.entries(value).map(([subKey, subValue]) => (
                    <div key={subKey} className="sla-subsection">
                      <h5 className="sla-subsection-title">{FIELD_LABELS[subKey] || subKey}</h5>
                      <table className="sla-field-table">
                        <tbody>
                          {Object.entries(subValue).map(([field, val]) => (
                            <tr key={field}>
                              <td className="field-label">{FIELD_LABELS[field] || field}</td>
                              <td className="field-value">{String(val)}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ))
                : (
                  <table className="sla-field-table">
                    <tbody>
                      {Object.entries(value).map(([field, val]) => (
                        <tr key={field}>
                          <td className="field-label">{FIELD_LABELS[field] || field}</td>
                          <td className="field-value">{String(val)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
            </div>
          );
        })}
      </div>
    );
  };

  // ─── Render ────────────────────────────────────────────────────
  if (!currentUser) {
    return <AuthPage onAuthSuccess={handleAuthSuccess} />;
  }

  return (
    <div className="app-container">
      {/* Header */}
      <header className="app-header">
        <div className="header-content">
          <div className="header-icon">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" width="28" height="28">
              <path d="M5 17h14M5 17a2 2 0 0 1-2-2V9a2 2 0 0 1 2-2h1l2-3h8l2 3h1a2 2 0 0 1 2 2v6a2 2 0 0 1-2 2M5 17l-1 2h2m12-2 1 2h-2" />
              <circle cx="7.5" cy="14" r="1.5" />
              <circle cx="16.5" cy="14" r="1.5" />
              <line x1="9" y1="10" x2="15" y2="10" />
            </svg>
          </div>
          <div>
            <h1>Car Lease Analyzer</h1>
            <p>AI-powered lease contract analysis & negotiation</p>
          </div>
        </div>
        {/* Car silhouette watermark */}
        <img className="header-car-bg" src={spCarSvg} alt="" aria-hidden="true" />
        <div style={{ display: 'flex', alignItems: 'center', paddingRight: '24px' }}>
          <div className="user-badge">
            <span><strong>Hi, {currentUser.name}</strong></span>
            <button className="logout-btn" onClick={handleLogout}>Sign out</button>
          </div>
        </div>
      </header>

      {/* Navigation Tabs */}
      <nav className="tab-nav">
        <button
          className={`tab-btn ${activeTab === 'extract' ? 'active' : ''}`}
          onClick={() => setActiveTab('extract')}
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
            <polyline points="14 2 14 8 20 8" />
            <path d="M9 15l3-3 3 3" />
            <line x1="12" y1="12" x2="12" y2="18" />
          </svg>
          Extract SLA
        </button>
        <button
          className={`tab-btn ${activeTab === 'vin' ? 'active' : ''}`}
          onClick={() => setActiveTab('vin')}
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M7 17h10M7 17a2 2 0 0 1-2-2V9l2-4h10l2 4v6a2 2 0 0 1-2 2M7 17l-1 2m12-2 1 2" />
            <circle cx="7" cy="13" r="1" />
            <circle cx="17" cy="13" r="1" />
          </svg>
          VIN Report
        </button>
        <button
          className={`tab-btn ${activeTab === 'chatbot' ? 'active' : ''}`}
          onClick={() => setActiveTab('chatbot')}
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
          </svg>
          Negotiate
        </button>
        <button
          className={`tab-btn ${activeTab === 'compare' ? 'active' : ''}`}
          onClick={() => { setActiveTab('compare'); fetchCompareRecords(); }}
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <rect x="2" y="3" width="8" height="18" rx="1" />
            <rect x="14" y="3" width="8" height="18" rx="1" />
            <path d="M10 12h4" />
          </svg>
          Compare
          {compareRecords.length > 0 && <span className="badge">{compareRecords.length}</span>}
        </button>
      </nav>

      {/* Main Content */}
      <main className="main-content">
        {/* ─── EXTRACT TAB ─── */}
        {activeTab === 'extract' && (
          <div className="tab-panel">
            {!selectedFile ? (
              <div
                className={`upload-zone ${isDragOver ? 'dragover' : ''}`}
                onClick={() => fileInputRef.current?.click()}
                onDragOver={(e) => {
                  e.preventDefault();
                  setIsDragOver(true);
                }}
                onDragLeave={() => setIsDragOver(false)}
                onDrop={(e) => {
                  e.preventDefault();
                  setIsDragOver(false);
                  handleFileSelect(e.dataTransfer.files[0]);
                }}
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                  <polyline points="14 2 14 8 20 8" />
                  <path d="M9 15l3-3 3 3" />
                  <line x1="12" y1="12" x2="12" y2="18" />
                </svg>
                <h3>Upload Car Lease Document</h3>
                <p>Drag and drop or click to browse</p>
                <span className="format-tag">JPG, PNG, PDF — up to 20 MB</span>
                <input
                  type="file"
                  ref={fileInputRef}
                  accept="image/*,.pdf"
                  onChange={(e) => handleFileSelect(e.target.files[0])}
                  hidden
                />
              </div>
            ) : (
              <div className="preview-area">
                <div className="preview-header">
                  <h3>Document Preview</h3>
                  <button className="btn-icon" onClick={handleRemoveFile} title="Remove file">
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <line x1="18" y1="6" x2="6" y2="18" />
                      <line x1="6" y1="6" x2="18" y2="18" />
                    </svg>
                  </button>
                </div>
                <div className="preview-image-wrapper">
                  {imagePreview ? (
                    <img src={imagePreview} alt="Document preview" />
                  ) : (
                    <div className="pdf-placeholder">
                      <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                        <polyline points="14 2 14 8 20 8" />
                      </svg>
                      <p>PDF loaded — preview unavailable</p>
                    </div>
                  )}
                </div>
                <p className="file-name">
                  {selectedFile.name} ({(selectedFile.size / 1024).toFixed(0)} KB)
                </p>
              </div>
            )}

            <button
              className="btn-primary extract-btn"
              disabled={!selectedFile || isLoading}
              onClick={handleExtract}
            >
              {isLoading ? (
                <>
                  <span className="spinner" />
                  Extracting SLA Data…
                </>
              ) : (
                <>
                  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <circle cx="11" cy="11" r="8" />
                    <line x1="21" y1="21" x2="16.65" y2="16.65" />
                  </svg>
                  Extract SLA Details
                </>
              )}
            </button>

            {statusMessage && <p className="status-msg">{statusMessage}</p>}
            {error && <div className="error-box">{error}</div>}

            {slaResult && (
              <div className="results-panel">
                <div className="results-header">
                  <h3>Extracted SLA Data</h3>
                  <div className="results-actions">
                    <button
                      className={`btn-toggle ${jsonViewMode === 'table' ? 'active' : ''}`}
                      onClick={() => setJsonViewMode('table')}
                    >
                      Table
                    </button>
                    <button
                      className={`btn-toggle ${jsonViewMode === 'json' ? 'active' : ''}`}
                      onClick={() => setJsonViewMode('json')}
                    >
                      JSON
                    </button>
                    <button
                      className="btn-secondary"
                      onClick={() => handleExportJSON(slaResult, `sla-${Date.now()}.json`)}
                    >
                      Export JSON
                    </button>
                  </div>
                </div>

                {jsonViewMode === 'table' ? (
                  renderSLATable(slaResult)
                ) : (
                  <pre className="json-output">{JSON.stringify(slaResult, null, 2)}</pre>
                )}

                {/* ─── Fairness Analysis ─── */}
                {(() => {
                  const { score, breakdown, rating, redFlags } = analyzeContract(slaResult);
                  return (
                    <div className="fairness-panel">
                      {/* Score Gauge */}
                      <div className="fairness-score-section">
                        <h3>Contract Fairness Score</h3>
                        <div className="score-gauge-wrapper">
                          <div className={`score-gauge score-${rating.toLowerCase().replace(/\s+/g, '-')}`}>
                            <svg viewBox="0 0 120 120" className="score-ring">
                              <circle cx="60" cy="60" r="52" fill="none" stroke="#e5e7eb" strokeWidth="10" />
                              <circle
                                cx="60" cy="60" r="52"
                                fill="none"
                                strokeWidth="10"
                                strokeLinecap="round"
                                strokeDasharray={`${(score / 100) * 327} 327`}
                                strokeDashoffset="0"
                                transform="rotate(-90 60 60)"
                                className="score-ring-fill"
                              />
                            </svg>
                            <div className="score-value">
                              <span className="score-number">{score}</span>
                              <span className="score-label">/100</span>
                            </div>
                          </div>
                          <div className={`score-rating rating-${rating.toLowerCase().replace(/\s+/g, '-')}`}>
                            {rating === 'Excellent' && '✅'}
                            {rating === 'Fair' && '👍'}
                            {rating === 'Needs Negotiation' && '⚠️'}
                            {rating === 'Poor' && '❌'}
                            {' '}{rating} Deal
                          </div>
                        </div>
                      </div>

                      {/* Score Breakdown */}
                      <div className="score-breakdown">
                        <h4>Score Breakdown</h4>
                        <table className="breakdown-table">
                          <thead>
                            <tr>
                              <th>Criterion</th>
                              <th>Value</th>
                              <th>Weight</th>
                              <th>Score</th>
                            </tr>
                          </thead>
                          <tbody>
                            {breakdown.map((item, i) => (
                              <tr key={i} className={item.score === null ? 'na-row' : ''}>
                                <td>{item.name}</td>
                                <td>{item.score === null ? '—' : String(item.value)}</td>
                                <td>{item.weight}%</td>
                                <td>
                                  {item.score === null ? (
                                    <span className="na-badge">N/A</span>
                                  ) : (
                                    <div className="score-bar-cell">
                                      <div className="score-bar">
                                        <div
                                          className={`score-bar-fill ${item.score >= 70 ? 'good' : item.score >= 40 ? 'fair' : 'poor'}`}
                                          style={{ width: `${item.score}%` }}
                                        />
                                      </div>
                                      <span>{item.score}</span>
                                    </div>
                                  )}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>

                      {/* Red Flags */}
                      {redFlags.length > 0 && (
                        <div className="red-flags-section">
                          <h4>⚠️ Red Flags ({redFlags.length})</h4>
                          <div className="red-flags-list">
                            {redFlags.map((flag, i) => (
                              <div key={i} className={`red-flag-card severity-${flag.severity}`}>
                                <div className="red-flag-header">
                                  <span className={`severity-badge ${flag.severity}`}>
                                    {flag.severity === 'high' ? '🔴' : flag.severity === 'medium' ? '🟠' : '🟡'}
                                    {' '}{flag.severity.toUpperCase()}
                                  </span>
                                  <span className="red-flag-type">{flag.type}</span>
                                </div>
                                <p className="red-flag-desc">{flag.description}</p>
                                <p className="red-flag-rec">
                                  <strong>Recommendation:</strong> {flag.recommendation}
                                </p>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {redFlags.length === 0 && (
                        <div className="no-red-flags">
                          <span>✅</span> No red flags detected — this contract looks reasonable.
                        </div>
                      )}

                      {/* Graph Visualizations */}
                      <ContractGraphs breakdown={breakdown} redFlags={redFlags} />
                    </div>
                  );
                })()}

                {/* ─── Market Price Comparison ─── */}
                {marketLoading && (
                  <div className="market-loading">
                    <div className="spinner" /> Fetching market price data...
                  </div>
                )}
                {marketData && !marketLoading && (() => {
                  const { score: mktScore, rating: mktRating, comparison } = calculateMarketScore(slaResult, marketData);
                  return (
                    <div className="market-panel">
                      <h3>📊 Market Price Comparison</h3>
                      <p className="market-subtitle">
                        Your contract vs. estimated market rates for a{' '}
                        <strong>
                          {marketData.year} {(marketData.make || '').charAt(0).toUpperCase() + (marketData.make || '').slice(1)}{' '}
                          {(marketData.model || '').charAt(0).toUpperCase() + (marketData.model || '').slice(1)}
                        </strong>
                        {' '}({marketData.vehicleClass?.replace(/_/g, ' ')}) — Est. MSRP: ${marketData.estimatedMSRP?.toLocaleString()}
                      </p>

                      <div className="market-score-bar">
                        <span className="market-score-label">Market Score</span>
                        <div className="market-score-track">
                          <div
                            className={`market-score-fill ${mktRating.toLowerCase().replace(/\s+/g, '-')}`}
                            style={{ width: `${mktScore}%` }}
                          />
                        </div>
                        <span className={`market-score-value ${mktRating.toLowerCase().replace(/\s+/g, '-')}`}>
                          {mktScore}/100 — {mktRating}
                        </span>
                      </div>

                      <div className="market-table-wrapper">
                        <table className="market-table">
                          <thead>
                            <tr>
                              <th>Metric</th>
                              <th>Your Contract</th>
                              <th>Market Low</th>
                              <th>Market Avg</th>
                              <th>Market High</th>
                              <th>Rating</th>
                            </tr>
                          </thead>
                          <tbody>
                            {comparison.map((row, i) => (
                              <tr key={i} className={`market-row-${row.status}`}>
                                <td>{row.label}</td>
                                <td className="contract-val">{row.contractValue}</td>
                                <td>{row.marketLow}</td>
                                <td className="market-avg">{row.marketAvg}</td>
                                <td>{row.marketHigh}</td>
                                <td>
                                  <span className={`market-badge ${row.status}`}>
                                    {row.status === 'good' ? '✅ Good' : row.status === 'fair' ? '⚠️ Fair' : row.status === 'poor' ? '❌ Poor' : '—'}
                                  </span>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                      <p className="market-disclaimer">
                        * Market estimates are based on vehicle class, MSRP, and standard lease calculations.
                        Actual market rates may vary by region, credit score, and dealer incentives.
                      </p>
                    </div>
                  );
                })()}
              </div>
            )}
          </div>
        )}

        {/* ─── VIN TAB ─── */}
        {activeTab === 'vin' && (
          <div className="tab-panel">
            <div className="vin-header">
              <div>
                <h2>VIN Report Viewer</h2>
                <p>Look up vehicle details and recall history.</p>
              </div>
            </div>

            {/* VIN Input */}
            <div className="vin-search-box">
              <div className="vin-input-row">
                <input
                  className="vin-input"
                  type="text"
                  placeholder="Enter 17-character VIN (e.g. 1HGCM82633A123456)"
                  value={vinInput}
                  maxLength={17}
                  onChange={(e) => {
                    setVinInput(e.target.value.toUpperCase());
                    setVinError('');
                  }}
                  onKeyDown={(e) => e.key === 'Enter' && handleVinLookup()}
                />
                <span className={`vin-char-count ${vinInput.length === 17 ? 'complete' : ''}`}>
                  {vinInput.length}/17
                </span>
                <button
                  className="btn-primary"
                  onClick={handleVinLookup}
                  disabled={vinLoading}
                >
                  {vinLoading ? (
                    <><span className="spinner" /> Looking up…</>
                  ) : (
                    'Get Report'
                  )}
                </button>
              </div>
              {vinError && <div className="error-box" style={{ marginTop: '10px' }}>{vinError}</div>}
            </div>

            {/* Report */}
            {vinReport && (
              <div className="vin-report">
                <div className="vin-report-title">
                  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <rect x="1" y="3" width="15" height="13" rx="2" />
                    <path d="M16 8h4l3 5v3h-7V8z" />
                    <circle cx="5.5" cy="18.5" r="2.5" />
                    <circle cx="18.5" cy="18.5" r="2.5" />
                  </svg>
                  <span>VIN: <strong>{vinReport.vin}</strong></span>
                </div>

                {/* Vehicle Details */}
                <div className="vin-section">
                  <h3 className="vin-section-title">Vehicle Details</h3>
                  {Object.keys(vinReport.vehicleDetails).length === 0 ? (
                    <p className="vin-no-data">No vehicle details found for this VIN.</p>
                  ) : (
                    <table className="sla-field-table">
                      <tbody>
                        {Object.entries(vinReport.vehicleDetails).map(([key, value]) => (
                          <tr key={key}>
                            <td className="field-label">{key}</td>
                            <td className="field-value">{value}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                </div>

                {/* Recall Information */}
                <div className="vin-section">
                  <h3 className="vin-section-title">
                    Recall History
                    <span className={`recall-badge ${vinReport.recalls.length > 0 ? 'has-recalls' : 'no-recalls'}`}>
                      {vinReport.recalls.length} recall{vinReport.recalls.length !== 1 ? 's' : ''}
                    </span>
                  </h3>
                  {vinReport.recalls.length === 0 ? (
                    <div className="vin-clear">
                      <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <polyline points="20 6 9 17 4 12" />
                      </svg>
                      No recalls found for this vehicle.
                    </div>
                  ) : (
                    <div className="recall-list">
                      {vinReport.recalls.map((recall, i) => (
                        <div key={i} className="recall-card">
                          <div className="recall-card-header">
                            <span className="recall-component">{recall.Component || 'Unknown Component'}</span>
                            <span className="recall-date">{recall.ReportReceivedDate || ''}</span>
                          </div>
                          {recall.Summary && (
                            <p><strong>Summary:</strong> {recall.Summary}</p>
                          )}
                          {recall.Remedy && (
                            <p><strong>Remedy:</strong> {recall.Remedy}</p>
                          )}
                          {recall.Consequence && (
                            <p><strong>Consequence:</strong> {recall.Consequence}</p>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Carfax redirect */}
                <div className="vin-section carfax-section">
                  <h3 className="vin-section-title">Full History Report</h3>
                  <p className="vin-no-data">Accident history and odometer data require a paid report.</p>
                  <button
                    className="btn-secondary carfax-btn"
                    onClick={() => window.open(`https://www.carfax.com/VehicleHistory/p/Report.cfx?vin=${vinReport.vin}`, '_blank')}
                  >
                    View Carfax Report (Paid)
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
        {/* ─── CHATBOT TAB ─── */}
        {activeTab === 'chatbot' && (
          <div className="tab-panel chatbot-panel">
            {/* Header */}
            <div className="chatbot-header">
              <div>
                <h2>Lease Negotiation Assistant</h2>
                <p>AI-powered guidance to understand and negotiate better lease terms.</p>
              </div>
              <div className="chatbot-header-actions">
                {(slaResult || selectedRecord) && (
                  <div className="chatbot-context-badge">
                    <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                      <polyline points="20 6 9 17 4 12" />
                    </svg>
                    Lease data in context
                  </div>
                )}
                {chatMessages.length > 0 && (
                  <button className="btn-secondary" onClick={() => setChatMessages([])}>
                    Clear chat
                  </button>
                )}
              </div>
            </div>

            {/* Chat window */}
            <div className="chat-window">
              {chatMessages.length === 0 ? (
                <div className="chat-welcome">
                  <div className="chat-welcome-icon">
                    <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                    </svg>
                  </div>
                  <h3>Lease Negotiation Advisor</h3>
                  <p>
                    I can help you understand lease clauses, spot what's negotiable, and craft better counter-offers.
                    {(slaResult || selectedRecord)
                      ? ' Your loaded lease data is available as context.'
                      : ' Upload and extract a lease document for context-aware advice.'}
                  </p>
                  <div className="chat-suggestions">
                    {SUGGESTED_PROMPTS.map((prompt) => (
                      <button
                        key={prompt}
                        className="suggestion-chip"
                        onClick={() => handleChatSend(prompt)}
                      >
                        {prompt}
                      </button>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="chat-messages">
                  {chatMessages.map((msg, i) => (
                    <div key={i} className={`chat-bubble-wrap ${msg.role}`}>
                      {msg.role === 'assistant' && (
                        <div className="chat-avatar">
                          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                          </svg>
                        </div>
                      )}
                      <div className={`chat-bubble ${msg.role}`}>
                        {msg.role === 'assistant' ? <ChatMarkdown text={msg.content} /> : msg.content}
                      </div>
                      {msg.role === 'user' && (
                        <div className="chat-avatar user-avatar">
                          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                            <circle cx="12" cy="7" r="4" />
                          </svg>
                        </div>
                      )}
                    </div>
                  ))}
                  {chatLoading && (
                    <div className="chat-bubble-wrap assistant">
                      <div className="chat-avatar">
                        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                        </svg>
                      </div>
                      <div className="chat-bubble assistant typing">
                        <span className="dot" />
                        <span className="dot" />
                        <span className="dot" />
                      </div>
                    </div>
                  )}
                  <div ref={chatEndRef} />
                </div>
              )}
            </div>

            {/* Input bar */}
            <div className="chat-input-bar">
              <input
                className="chat-input"
                type="text"
                placeholder="Ask about lease terms, negotiation tactics…"
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleChatSend();
                  }
                }}
                disabled={chatLoading}
              />
              <button
                className="btn-primary chat-send-btn"
                onClick={() => handleChatSend()}
                disabled={!chatInput.trim() || chatLoading}
                title="Send message"
              >
                {chatLoading ? (
                  <span className="spinner" />
                ) : (
                  <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <line x1="22" y1="2" x2="11" y2="13" />
                    <polygon points="22 2 15 22 11 13 2 9 22 2" />
                  </svg>
                )}
              </button>
            </div>
          </div>
        )}

        {/* ─── COMPARE TAB ─── */}
        {activeTab === 'compare' && (() => {
          const toggleCompare = (id) => {
            setCompareSelected((prev) =>
              prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
            );
          };

          const selectedContracts = compareRecords.filter((r) => compareSelected.includes(r.id));

          const comparedData = selectedContracts.map((r) => {
            const analysis = analyzeContract(r.slaData);
            return { ...r, analysis };
          });

          const bestDeal = comparedData.length >= 2
            ? comparedData.reduce((best, c) => (c.analysis.score > best.analysis.score ? c : best), comparedData[0])
            : null;

          const COMPARE_FIELDS = [
            { label: 'Vehicle', get: (d) => `${d?.vehicle_details?.year || ''} ${d?.vehicle_details?.make || ''} ${d?.vehicle_details?.model || ''}`.trim() || '—' },
            { label: 'Monthly Payment', get: (d) => d?.lease_terms?.monthly_payment || '—' },
            { label: 'Down Payment', get: (d) => d?.lease_terms?.down_payment || '—' },
            { label: 'Duration', get: (d) => d?.lease_terms?.duration_months ? `${d.lease_terms.duration_months} months` : '—' },
            { label: 'Total Lease Cost', get: (d) => d?.lease_terms?.total_lease_cost || '—' },
            { label: 'Annual Mileage Limit', get: (d) => d?.mileage_terms?.annual_mileage_limit || '—' },
            { label: 'Excess Mileage Charge', get: (d) => d?.mileage_terms?.excess_mileage_charge_per_mile || '—' },
            { label: 'Security Deposit', get: (d) => d?.lease_terms?.security_deposit || '—' },
            { label: 'Early Termination Fee', get: (d) => d?.penalties?.early_termination_fee || '—' },
            { label: 'Late Payment Fee', get: (d) => d?.penalties?.late_payment_fee || '—' },
            { label: 'Residual Value', get: (d) => d?.end_of_lease_options?.residual_value || '—' },
            { label: 'Purchase Option', get: (d) => d?.end_of_lease_options?.purchase_option || '—' },
            { label: 'Maintenance', get: (d) => d?.sla_obligations?.maintenance_responsibility || '—' },
            { label: 'Insurance', get: (d) => d?.sla_obligations?.insurance_requirements || '—' },
          ];

          return (
            <div className="tab-panel">
              <div className="compare-header">
                <div>
                  <h2>Compare Contracts</h2>
                  <p>Select contracts from your history to compare side-by-side and find the best deal.</p>
                </div>
                <div className="compare-header-actions">
                  {compareSelected.length >= 2 && (
                    <button className="btn-primary" onClick={() => setShowComparison(true)}>
                      <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <rect x="2" y="3" width="8" height="18" rx="1" />
                        <rect x="14" y="3" width="8" height="18" rx="1" />
                      </svg>
                      Compare ({compareSelected.length})
                    </button>
                  )}
                  {compareSelected.length > 0 && (
                    <button className="btn-secondary" onClick={() => { setCompareSelected([]); setShowComparison(false); }}>
                      Clear Selection
                    </button>
                  )}
                </div>
              </div>

              {/* Contract History List */}
              {compareLoading ? (
                <div className="empty-state">
                  <span className="spinner-sm" style={{ width: 32, height: 32 }} />
                  <h3>Loading contracts from database…</h3>
                </div>
              ) : compareRecords.length === 0 ? (
                <div className="empty-state">
                  <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                    <polyline points="14 2 14 8 20 8" />
                  </svg>
                  <h3>No Contracts Yet</h3>
                  <p>Upload and extract lease documents in the Extract SLA tab to start comparing.</p>
                </div>
              ) : (
                <>
                  <div className="compare-history-grid">
                    {compareRecords.map((rec) => {
                      const { score, rating } = analyzeContract(rec.slaData);
                      const isSelected = compareSelected.includes(rec.id);
                      const vehicle = `${rec.slaData?.vehicle_details?.year || ''} ${rec.slaData?.vehicle_details?.make || ''} ${rec.slaData?.vehicle_details?.model || ''}`.trim();
                      return (
                        <div
                          key={rec.id}
                          className={`compare-card ${isSelected ? 'selected' : ''}`}
                          onClick={() => toggleCompare(rec.id)}
                        >
                          <div className="compare-card-check">
                            <div className={`checkbox ${isSelected ? 'checked' : ''}`}>
                              {isSelected && (
                                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                                  <polyline points="20 6 9 17 4 12" />
                                </svg>
                              )}
                            </div>
                          </div>
                          <div className="compare-card-body">
                            <div className="compare-card-title">{vehicle || rec.fileName}</div>
                            <div className="compare-card-meta">
                              <span>{rec.fileName}</span>
                              <span>{new Date(rec.timestamp).toLocaleDateString()}</span>
                            </div>
                            <div className="compare-card-details">
                              {rec.slaData?.lease_terms?.monthly_payment && (
                                <span className="compare-detail-chip">{rec.slaData.lease_terms.monthly_payment}/mo</span>
                              )}
                              {rec.slaData?.lease_terms?.duration_months && (
                                <span className="compare-detail-chip">{rec.slaData.lease_terms.duration_months} months</span>
                              )}
                              {rec.slaData?.mileage_terms?.annual_mileage_limit && (
                                <span className="compare-detail-chip">{rec.slaData.mileage_terms.annual_mileage_limit} mi/yr</span>
                              )}
                            </div>
                          </div>
                          <div className="compare-card-score">
                            <div className={`mini-score score-${rating.toLowerCase().replace(/\s+/g, '-')}`}>
                              {score}
                            </div>
                            <span className="mini-score-label">{rating}</span>
                          </div>
                        </div>
                      );
                    })}
                  </div>

                  {/* Side-by-Side Comparison */}
                  {showComparison && comparedData.length >= 2 && (
                    <div className="comparison-panel">
                      <div className="comparison-panel-header">
                        <h3>Side-by-Side Comparison</h3>
                        <button className="btn-icon" onClick={() => setShowComparison(false)} title="Close comparison">
                          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <line x1="18" y1="6" x2="6" y2="18" />
                            <line x1="6" y1="6" x2="18" y2="18" />
                          </svg>
                        </button>
                      </div>

                      {/* Best Deal Banner */}
                      {bestDeal && (
                        <div className="best-deal-banner">
                          <div className="best-deal-icon">
                            <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                              <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
                            </svg>
                          </div>
                          <div>
                            <strong>Best Deal:</strong>{' '}
                            {`${bestDeal.slaData?.vehicle_details?.year || ''} ${bestDeal.slaData?.vehicle_details?.make || ''} ${bestDeal.slaData?.vehicle_details?.model || ''}`.trim() || bestDeal.fileName}
                            {' — '}
                            <span className="best-deal-score">Fairness Score: {bestDeal.analysis.score}/100 ({bestDeal.analysis.rating})</span>
                          </div>
                        </div>
                      )}

                      {/* Score Overview */}
                      <div className="comparison-scores">
                        {comparedData.map((c) => {
                          const isBest = bestDeal && c.id === bestDeal.id;
                          const vehicle = `${c.slaData?.vehicle_details?.year || ''} ${c.slaData?.vehicle_details?.make || ''} ${c.slaData?.vehicle_details?.model || ''}`.trim();
                          return (
                            <div key={c.id} className={`comparison-score-card ${isBest ? 'is-best' : ''}`}>
                              {isBest && <div className="best-ribbon">Best Deal</div>}
                              <div className="comparison-score-title">{vehicle || c.fileName}</div>
                              <div className={`comparison-gauge score-${c.analysis.rating.toLowerCase().replace(/\s+/g, '-')}`}>
                                <svg viewBox="0 0 120 120" className="score-ring">
                                  <circle cx="60" cy="60" r="52" fill="none" stroke="#e5e7eb" strokeWidth="10" />
                                  <circle
                                    cx="60" cy="60" r="52"
                                    fill="none"
                                    strokeWidth="10"
                                    strokeLinecap="round"
                                    strokeDasharray={`${(c.analysis.score / 100) * 327} 327`}
                                    strokeDashoffset="0"
                                    transform="rotate(-90 60 60)"
                                    className="score-ring-fill"
                                  />
                                </svg>
                                <div className="score-value">
                                  <span className="score-number">{c.analysis.score}</span>
                                  <span className="score-label">/100</span>
                                </div>
                              </div>
                              <div className={`score-rating rating-${c.analysis.rating.toLowerCase().replace(/\s+/g, '-')}`}>
                                {c.analysis.rating}
                              </div>
                              {c.analysis.redFlags.length > 0 && (
                                <div className="comparison-flags-count">
                                  ⚠️ {c.analysis.redFlags.length} red flag{c.analysis.redFlags.length !== 1 ? 's' : ''}
                                </div>
                              )}
                            </div>
                          );
                        })}
                      </div>

                      {/* Comparison Table */}
                      <div className="comparison-table-wrapper">
                        <table className="comparison-table">
                          <thead>
                            <tr>
                              <th className="compare-field-col">Field</th>
                              {comparedData.map((c) => {
                                const vehicle = `${c.slaData?.vehicle_details?.year || ''} ${c.slaData?.vehicle_details?.make || ''} ${c.slaData?.vehicle_details?.model || ''}`.trim();
                                const isBest = bestDeal && c.id === bestDeal.id;
                                return (
                                  <th key={c.id} className={isBest ? 'best-col' : ''}>
                                    {vehicle || c.fileName}
                                    {isBest && <span className="best-star"> ★</span>}
                                  </th>
                                );
                              })}
                            </tr>
                          </thead>
                          <tbody>
                            <tr className="score-row">
                              <td className="compare-field-col"><strong>Fairness Score</strong></td>
                              {comparedData.map((c) => {
                                const isBest = bestDeal && c.id === bestDeal.id;
                                return (
                                  <td key={c.id} className={isBest ? 'best-col' : ''}>
                                    <span className={`inline-score score-${c.analysis.rating.toLowerCase().replace(/\s+/g, '-')}`}>
                                      {c.analysis.score}/100
                                    </span>
                                  </td>
                                );
                              })}
                            </tr>
                            {COMPARE_FIELDS.map((field) => (
                              <tr key={field.label}>
                                <td className="compare-field-col">{field.label}</td>
                                {comparedData.map((c) => {
                                  const isBest = bestDeal && c.id === bestDeal.id;
                                  return (
                                    <td key={c.id} className={isBest ? 'best-col' : ''}>
                                      {field.get(c.slaData)}
                                    </td>
                                  );
                                })}
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>

                      {/* Red Flags Comparison */}
                      {comparedData.some((c) => c.analysis.redFlags.length > 0) && (
                        <div className="comparison-flags-section">
                          <h4>Red Flags Comparison</h4>
                          <div className="comparison-flags-grid">
                            {comparedData.map((c) => {
                              const vehicle = `${c.slaData?.vehicle_details?.year || ''} ${c.slaData?.vehicle_details?.make || ''} ${c.slaData?.vehicle_details?.model || ''}`.trim();
                              return (
                                <div key={c.id} className="comparison-flags-col">
                                  <h5>{vehicle || c.fileName}</h5>
                                  {c.analysis.redFlags.length === 0 ? (
                                    <div className="no-red-flags">✅ No red flags</div>
                                  ) : (
                                    c.analysis.redFlags.map((flag, i) => (
                                      <div key={i} className={`red-flag-card severity-${flag.severity}`}>
                                        <div className="red-flag-header">
                                          <span className={`severity-badge ${flag.severity}`}>
                                            {flag.severity === 'high' ? '🔴' : flag.severity === 'medium' ? '🟠' : '🟡'}
                                            {' '}{flag.severity.toUpperCase()}
                                          </span>
                                        </div>
                                        <p className="red-flag-desc">{flag.description}</p>
                                      </div>
                                    ))
                                  )}
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </>
              )}
            </div>
          );
        })()}
      </main>

      <footer className="app-footer">
        <p>🚗 Car Lease Analyzer</p>
      </footer>
    </div>
  );
}

export default App;
