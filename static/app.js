const form = document.querySelector('#quote-form');
const status = document.querySelector('#status');
const button = document.querySelector('#draft-button');
const proposal = document.querySelector('#proposal');
const emptyState = document.querySelector('#empty-state');
const copyButton = document.querySelector('#copy-button');
const currencySymbols = { USD: '$', INR: '₹', EUR: '€', GBP: '£', CAD: '$', AUD: '$' };

function formatMoney(value, currency) {
  return new Intl.NumberFormat(undefined, { style: 'currency', currency }).format(value);
}

function updateEstimate() {
  const data = new FormData(form);
  const currency = data.get('currency');
  const total = (Number(data.get('rate')) || 0) * (Number(data.get('hours')) || 0) + (Number(data.get('expenses')) || 0);
  document.querySelector('#estimate').textContent = formatMoney(total, currency);
  document.querySelector('#currency-symbol').textContent = currencySymbols[currency] || currency;
  document.querySelector('#expense-symbol').textContent = currencySymbols[currency] || currency;
}

form.addEventListener('input', updateEstimate);
form.addEventListener('change', updateEstimate);
updateEstimate();

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  status.textContent = '';
  button.disabled = true;
  button.querySelector('span:first-child').textContent = 'Writing with local AI…';
  try {
    const response = await fetch('/api/draft', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(Object.fromEntries(new FormData(form))),
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || 'Could not draft the proposal.');
    proposal.textContent = result.proposal || 'The model returned an empty draft. Please try again.';
    proposal.hidden = false;
    emptyState.hidden = true;
    document.querySelector('#result-meta').hidden = false;
    document.querySelector('#model-name').textContent = result.model;
    document.querySelector('#result-total').textContent = formatMoney(result.total, result.currency);
    document.querySelector('#result-title').textContent = `Proposal for ${form.elements.client.value.trim()}`;
    copyButton.disabled = false;
  } catch (error) {
    status.textContent = error.message;
  } finally {
    button.disabled = false;
    button.querySelector('span:first-child').textContent = 'Draft my proposal';
  }
});

copyButton.addEventListener('click', async () => {
  await navigator.clipboard.writeText(proposal.textContent);
  copyButton.textContent = 'Copied';
  setTimeout(() => { copyButton.textContent = 'Copy draft'; }, 1500);
});
