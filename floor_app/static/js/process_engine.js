/* KIA FLOOR PROCESS VALIDATION - CLIENT JAVASCRIPT ENGINE */

function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

const csrftoken = getCookie('csrftoken');

// Helper to show toast messages
function showToast(message, type = 'success') {
  const toast = document.getElementById('toastNotice');
  if (!toast) return;
  toast.innerText = message;
  toast.style.backgroundColor = type === 'success' ? '#10B981' : '#EF4444';
  toast.style.display = 'block';
  setTimeout(() => {
    toast.style.display = 'none';
  }, 4000);
}

// Generate new barcode
function generateNewBarcode() {
  fetch('/api/generate-barcode/')
    .then(res => res.json())
    .then(data => {
      if (data.status === 'ok') {
        const input = document.getElementById('barcodeInput');
        if (input) {
          input.value = data.barcode;
          showToast(`Generated new barcode: ${data.barcode}`);
          // Reload scenario for new barcode
          const scenarioSelect = document.getElementById('scenarioSelect');
          if (scenarioSelect) {
            loadScenarioData(scenarioSelect.value);
          }
        }
      }
    })
    .catch(err => console.error(err));
}

// Load dynamic demo scenario data
function loadScenarioData(scenario) {
  const barcodeInput = document.getElementById('barcodeInput');
  const barcode = barcodeInput ? barcodeInput.value : 'DEMO20260924-001';
  const processCode = window.currentProcessCode || 'P10';

  const selectElem = document.getElementById('scenarioSelect');
  if (selectElem) {
    if (scenario === 'SUCCESS') {
      selectElem.className = 'select-scenario success-mode';
    } else {
      selectElem.className = 'select-scenario fail-mode';
    }
  }

  fetch(`/api/demo-scenario/?process_code=${processCode}&scenario=${scenario}&barcode=${barcode}`)
    .then(res => res.json())
    .then(res => {
      if (res.status === 'ok') {
        renderDemoData(res.data);
      }
    })
    .catch(err => console.error(err));
}

function renderDemoData(data) {
  // Update fields if present
  if (data.options) {
    for (const [key, val] of Object.entries(data.options)) {
      const elem = document.getElementById(`opt_${key}`);
      if (elem) {
        elem.value = val;
      }
    }
  }

  // Update subparts table
  const subpartsTbody = document.getElementById('subpartsTbody');
  if (subpartsTbody && data.subparts) {
    subpartsTbody.innerHTML = '';
    data.subparts.forEach((item, idx) => {
      const isOk = item.result === 'OK';
      const badgeClass = isOk ? 'pill-pass' : 'pill-fail';
      const row = `
        <tr>
          <td class="fw-bold">${idx + 1}</td>
          <td><code>${item.code}</code></td>
          <td>${item.desc}</td>
          <td><span class="status-pill ${badgeClass}">${item.result}</span></td>
        </tr>
      `;
      subpartsTbody.insertAdjacentHTML('beforeend', row);
    });
  }

  // Update screws table
  const screwsTbody = document.getElementById('screwsTbody');
  if (screwsTbody && data.screws) {
    screwsTbody.innerHTML = '';
    data.screws.forEach((sc) => {
      const isOk = sc.status === 'OK';
      const badgeClass = isOk ? 'pill-pass' : 'pill-fail';
      const row = `
        <tr>
          <td class="fw-bold">${sc.type}</td>
          <td>${sc.required}</td>
          <td><strong>${sc.scanned}</strong></td>
          <td><span class="status-pill ${badgeClass}">${sc.status}</span></td>
        </tr>
      `;
      screwsTbody.insertAdjacentHTML('beforeend', row);
    });
  }

  // Failure banner
  const failBanner = document.getElementById('failBanner');
  const failReasonText = document.getElementById('failReasonText');
  if (failBanner && failReasonText) {
    if (data.result === 'FAIL') {
      failReasonText.innerText = data.failure_reason || 'Validation error detected.';
      failBanner.style.display = 'block';
    } else {
      failBanner.style.display = 'none';
    }
  }
}

// Submit Process Result
function submitProcessResult() {
  const barcodeInput = document.getElementById('barcodeInput');
  const scenarioSelect = document.getElementById('scenarioSelect');
  const failReasonText = document.getElementById('failReasonText');

  const barcode = barcodeInput ? barcodeInput.value : '';
  const processCode = window.currentProcessCode || 'P10';
  const demoResult = scenarioSelect ? scenarioSelect.value : 'SUCCESS';
  const failureReason = failReasonText ? failReasonText.innerText : '';

  const payload = {
    barcode: barcode,
    process_code: processCode,
    demo_result: demoResult,
    failure_reason: failureReason
  };

  fetch('/api/submit-process/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': csrftoken
    },
    body: JSON.stringify(payload)
  })
    .then(res => res.json())
    .then(data => {
      if (data.status === 'ok') {
        if (data.result === 'PASS') {
          showToast(`SUCCESS: ${processCode} passed! Unlocking next process...`, 'success');
          setTimeout(() => {
            if (data.next_process) {
              window.location.href = `/validation/${data.next_process}/?barcode=${barcode}`;
            } else {
              window.location.href = `/dashboard/`;
            }
          }, 1200);
        } else {
          showToast(`FAIL: ${processCode} recorded as NG condition! Next process locked.`, 'error');
        }
      } else {
        showToast(`Error: ${data.message}`, 'error');
      }
    })
    .catch(err => {
      console.error(err);
      showToast('Network error during submission', 'error');
    });
}

// Operator Switcher
function switchOperator(opId) {
  const formData = new FormData();
  formData.append('operator_id', opId);

  fetch('/api/switch-operator/', {
    method: 'POST',
    headers: {
      'X-CSRFToken': csrftoken
    },
    body: formData
  })
    .then(res => res.json())
    .then(data => {
      if (data.status === 'ok') {
        location.reload();
      }
    });
}
