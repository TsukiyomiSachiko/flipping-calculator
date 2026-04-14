// Format numbers with K/M/B suffixes
export const formatNumber = (num) => {
  if (!num) return '0';
  
  const absNum = Math.abs(num);
  
  if (absNum >= 1_000_000_000) {
    return `${(num / 1_000_000_000).toFixed(1)}B`;
  }
  if (absNum >= 1_000_000) {
    return `${(num / 1_000_000).toFixed(1)}M`;
  }
  if (absNum >= 1_000) {
    return `${(num / 1_000).toFixed(1)}K`;
  }
  return num.toLocaleString();
};

// Format GP (gold pieces)
export const formatGP = (num) => {
  return `${formatNumber(num)} gp`;
};

// Format exact GP (no K/M/B shortening - for per-item prices)
export const formatExactGP = (num) => {
  if (!num && num !== 0) return '0 gp';
  return `${Math.round(num).toLocaleString()} gp`;
};

// Format percentage
export const formatPercent = (num) => {
  if (!num) return '0%';
  return `${num.toFixed(2)}%`;
};

// Format ROI with color
export const formatROI = (roi) => {
  if (!roi) return { text: '0%', color: 'text-gray-400' };
  
  const color = roi >= 10 ? 'text-osrs-green' : 
                roi >= 5 ? 'text-yellow-400' : 
                roi >= 0 ? 'text-gray-400' : 'text-osrs-red';
  
  return {
    text: formatPercent(roi),
    color,
  };
};

// Format volume indicator (aligned with backend thresholds)
export const getVolumeIndicator = (volume) => {
  if (!volume) return { emoji: '⚪', color: 'text-gray-400', text: 'Unknown' };
  
  if (volume >= 50000) return { emoji: '🟢', color: 'text-green-400', text: 'High' };
  if (volume >= 5000) return { emoji: '🟡', color: 'text-yellow-400', text: 'Medium' };
  if (volume >= 1000) return { emoji: '🔴', color: 'text-red-400', text: 'Low' };
  return { emoji: '⚪', color: 'text-gray-400', text: 'Very Low' };
};

// Parse user input for cash (supports K, M, B)
export const parseCash = (input) => {
  if (!input) return 0;
  
  const str = input.toString().toUpperCase().trim();
  const num = parseFloat(str);
  
  if (str.endsWith('B')) return num * 1_000_000_000;
  if (str.endsWith('M')) return num * 1_000_000;
  if (str.endsWith('K')) return num * 1_000;
  
  return num;
};

// Format date/time
export const formatDateTime = (dateStr) => {
  if (!dateStr) return '';
  const date = new Date(dateStr);
  return date.toLocaleString();
};

// Format relative time
export const formatRelativeTime = (dateStr) => {
  if (!dateStr) return '';
  
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now - date;
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);
  
  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  
  return date.toLocaleDateString();
};

// Class name helper
export const cn = (...classes) => {
  return classes.filter(Boolean).join(' ');
};