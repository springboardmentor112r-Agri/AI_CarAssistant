/**
 * Lightweight markdown-to-JSX renderer for chat bubbles.
 * Supports: **bold**, *italic*, bullet lists (- / •), numbered lists, line breaks.
 * No external dependencies.
 */

export default function ChatMarkdown({ text }) {
  if (!text) return null;

  const lines = text.split('\n');
  const elements = [];
  let listItems = [];
  let listType = null; // 'ul' | 'ol'

  const flushList = () => {
    if (listItems.length > 0) {
      const Tag = listType === 'ol' ? 'ol' : 'ul';
      elements.push(<Tag key={`list-${elements.length}`}>{listItems}</Tag>);
      listItems = [];
      listType = null;
    }
  };

  lines.forEach((line, i) => {
    const trimmed = line.trim();

    // Bullet list: - item or • item or * item (but not **bold**)
    const bulletMatch = trimmed.match(/^[-•]\s+(.+)/);
    // Numbered list: 1. item, 2) item
    const numberMatch = trimmed.match(/^\d+[.)]\s+(.+)/);

    if (bulletMatch) {
      if (listType !== 'ul') flushList();
      listType = 'ul';
      listItems.push(<li key={`li-${i}`}>{formatInline(bulletMatch[1])}</li>);
    } else if (numberMatch) {
      if (listType !== 'ol') flushList();
      listType = 'ol';
      listItems.push(<li key={`li-${i}`}>{formatInline(numberMatch[1])}</li>);
    } else {
      flushList();
      if (trimmed === '') {
        // Empty line = paragraph break (only if not consecutive)
        if (elements.length > 0) {
          elements.push(<br key={`br-${i}`} />);
        }
      } else {
        elements.push(
          <p key={`p-${i}`} style={{ margin: '0 0 4px 0' }}>
            {formatInline(trimmed)}
          </p>
        );
      }
    }
  });

  flushList();
  return <>{elements}</>;
}

/**
 * Parse inline markdown: **bold**, *italic*, `code`
 */
function formatInline(text) {
  // Split on **bold**, *italic*, and `code` patterns
  const parts = [];
  const regex = /(\*\*(.+?)\*\*|\*(.+?)\*|`(.+?)`)/g;
  let lastIndex = 0;
  let match;

  while ((match = regex.exec(text)) !== null) {
    // Push text before the match
    if (match.index > lastIndex) {
      parts.push(text.slice(lastIndex, match.index));
    }

    if (match[2]) {
      // **bold**
      parts.push(<strong key={match.index}>{match[2]}</strong>);
    } else if (match[3]) {
      // *italic*
      parts.push(<em key={match.index}>{match[3]}</em>);
    } else if (match[4]) {
      // `code`
      parts.push(<code key={match.index} className="chat-inline-code">{match[4]}</code>);
    }

    lastIndex = match.index + match[0].length;
  }

  // Push remaining text
  if (lastIndex < text.length) {
    parts.push(text.slice(lastIndex));
  }

  return parts.length > 0 ? parts : text;
}
