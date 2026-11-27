// Exécution : node tests/test_frontend_uncertainty.cjs (aucune dépendance).
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.resolve(__dirname, '..');
const context = {};
vm.runInNewContext(fs.readFileSync(path.join(root, 'frontend/assets/app.js'), 'utf8') + '\nthis.NC = NC;', context);
const verdict = {label: 'faux', uncertainty: 0.15, explanation: '<exemple>', citations: ['p1']};
const nli = context.NC.verdictBox(verdict, {used: 'llm', uncertainty_source: 'nli'});
assert.ok(nli.includes('incertitude estimée par le NLI (indicateur, non calibré)'));
assert.ok(nli.includes('0,15') && nli.includes('width:15%'));
assert.ok(nli.includes('&lt;exemple&gt;') && nli.includes('p1'));
for (const uncertainty_source of ['fixe', undefined, 'inconnue']) {
  const fixed = context.NC.verdictBox({...verdict, uncertainty: 0.4}, {used: 'llm', uncertainty_source});
  assert.ok(fixed.includes('incertitude non calibrée'));
  assert.ok(!fixed.includes('class="meter"') && !fixed.includes('0,40'));
}
const fallback = context.NC.verdictBox(verdict, {used: 'gabarit', uncertainty_source: 'nli'});
assert.ok(fallback.includes("indice d'incertitude (non calibré)"));
assert.ok(!fallback.includes('estimée par le NLI'));
const abstention = context.NC.verdictBox({...verdict, label: 'preuves_insuffisantes', abstained: true, citations: []}, {used: 'llm', uncertainty_source: 'nli'});
assert.ok(abstention.includes('abstention') && !abstention.includes('Verdict sans citation'));
for (const page of ['index.html', 'lot-d.html']) {
  const html = fs.readFileSync(path.join(root, 'frontend', page), 'utf8');
  assert.ok(html.includes('NC.verdictBox('));
  for (const m of html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g)) {
    if (m[1].trim()) new vm.Script(m[1], {filename: page});
  }
}
console.log('OK : jauge NLI, valeur fixe masquée, repli, abstention, échappement et syntaxe des pages.');
