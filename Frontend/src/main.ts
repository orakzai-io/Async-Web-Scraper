import { submitUrls, getJobs, getDownloadUrl } from './api';

// Elements
const urlInput = document.getElementById('urlInput') as HTMLInputElement;
const addUrlBtn = document.getElementById('addUrlBtn') as HTMLButtonElement;
const submitBtn = document.getElementById('submitBtn') as HTMLButtonElement;
const urlListEl = document.getElementById('urlList') as HTMLUListElement;
const urlCountEl = document.getElementById('urlCount') as HTMLSpanElement;
const jobsListEl = document.getElementById('jobsList') as HTMLTableSectionElement;
const downloadBtn = document.getElementById('downloadBtn') as HTMLButtonElement;

// State
let urlsToScrape: string[] = [];

// Events
addUrlBtn.addEventListener('click', addUrl);
urlInput.addEventListener('keypress', (e) => { 
  if (e.key === 'Enter') addUrl(); 
});
submitBtn.addEventListener('click', submitScrape);

function addUrl() {
  let url = urlInput.value.trim();
  if (!url) return; // checks if the url is empty
  if (!url.startsWith('http://') && !url.startsWith('https://')) {
    url = 'https://' + url; // if the url is not starting with http:// or https://, it will add https:// to the url
  }
  
  urlsToScrape.push(url); // adds the url to the urlsToScrape array
  urlInput.value = '';
  renderUrlList();
}

function removeUrl(index: number) {
  urlsToScrape.splice(index, 1);
  renderUrlList();
}

// Need to attach to window so HTML onclick handler works
(window as any).removeUrl = removeUrl;

function renderUrlList() {
  urlCountEl.textContent = urlsToScrape.length.toString();
  submitBtn.disabled = urlsToScrape.length === 0;

  if (urlsToScrape.length === 0) {
    urlListEl.innerHTML = '<li class="empty-list-msg">No URLs added yet.</li>';
    return;
  }

  urlListEl.innerHTML = '';
  urlsToScrape.forEach((url, i) => {
    const li = document.createElement('li');
    
    const span = document.createElement('span');
    span.textContent = url;
    li.appendChild(span);
    
    const btn = document.createElement('button');
    btn.innerHTML = '&times;';
    btn.onclick = () => removeUrl(i);
    li.appendChild(btn);
    
    urlListEl.appendChild(li);
  });
}

async function submitScrape() {
  if (urlsToScrape.length === 0) return;

  submitBtn.disabled = true;
  submitBtn.textContent = 'Submitting...';

  try {
    await submitUrls(urlsToScrape);
    
    // Clear list on success
    urlsToScrape = [];
    renderUrlList();
    fetchJobs(); // Update UI immediately
  } catch (error) {
    alert('Error submitting urls. Ensure your backend is running.');
    console.error(error);
  } finally {
    submitBtn.textContent = 'Start Extraction';
  }
}

// Polling and rendering jobs
function getStatusHtml(status: string) {
  let icon = '';
  if (status === 'completed') {
    icon = `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" style="margin-right:4px"><polyline points="20 6 9 17 4 12"></polyline></svg>`;
  } else if (status === 'processing') {
    icon = `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right:4px" class="spin-icon"><line x1="12" y1="2" x2="12" y2="6"></line><line x1="12" y1="18" x2="12" y2="22"></line><line x1="4.93" y1="4.93" x2="7.76" y2="7.76"></line><line x1="16.24" y1="16.24" x2="19.07" y2="19.07"></line><line x1="2" y1="12" x2="6" y2="12"></line><line x1="18" y1="12" x2="22" y2="12"></line><line x1="4.93" y1="19.07" x2="7.76" y2="16.24"></line><line x1="16.24" y1="7.76" x2="19.07" y2="4.93"></line></svg>`;
  } else if (status === 'failed') {
    icon = `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right:4px"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>`;
  } else if (status === 'pending') {
    icon = `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right:4px"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>`;
  }

  return `<span class="job-status status-${status}" style="display:inline-flex; align-items:center;">${icon}${status}</span>`;
}

async function fetchJobs() {
  try {
    const jobs = await getJobs();
    renderJobs(jobs);
  } catch (e) {
    console.error('API connection failed:', e);
  }
}

function renderJobs(jobs: Record<string, any>) {
  const entries = Object.entries(jobs);
  if (entries.length === 0) {
    jobsListEl.innerHTML = '<tr><td colspan="3" class="empty-state" style="text-align: center; padding: 1.5rem;">No URLs processing right now.</td></tr>';
    downloadBtn.style.display = 'none';
    return;
  }

  let allCompleted = true;
  let rowsHtml = '';
  let counter = 1;

  for (const [, job] of entries) {
    if (job.status !== 'completed') {
      allCompleted = false;
    }
    
    // job.urls is a map of url -> status
    const urlsAndStatuses = Object.entries(job.urls || {}) as [string, string][];
    for (const [url, status] of urlsAndStatuses) {
      rowsHtml += `
        <tr class="row-${status}">
          <td>${counter++}</td>
          <td style="word-break: break-all;"><a href="${url}" target="_blank" style="color: var(--secondary); text-decoration: none;">${url}</a></td>
          <td>${getStatusHtml(status)}</td>
        </tr>
      `;
    }
  }

  jobsListEl.innerHTML = rowsHtml;

  if (allCompleted && entries.length > 0) {
    downloadBtn.style.display = 'inline-block';
    downloadBtn.onclick = () => {
      window.location.href = getDownloadUrl();
      setTimeout(() => {
        window.location.reload();
      }, 2000); // Reload after 2s to allow download to fire
    };
  } else {
    downloadBtn.style.display = 'none';
  }
}

// Download logic handled inside renderJobs

// Initial setup
renderUrlList();
setInterval(fetchJobs, 3000); // Polling every 3s
fetchJobs();
