export default function WhatIfPage() {
  return (
    <div className="space-y-6">
      <h1 className="font-serif text-3xl text-oliva-900">Simulador What-if</h1>
      <p className="text-sm text-oliva-600">3 paneles comparados, snapshots no destructivos. Pendiente Fase 5.</p>
      <ul className="list-disc pl-6 text-sm text-oliva-600">
        <li>¿Y si no proceso tomasa esta temporada y amplío alperujo?</li>
        <li>¿Y si el licopeno cae 30%?</li>
        <li>¿Y si Olivero 3 sube de 500 a 2.000 ton?</li>
        <li>¿Y si compro la 2ª línea PEF en año 2 en vez de año 3?</li>
        <li>¿Y si entran nuevas certificaciones?</li>
      </ul>
    </div>
  );
}
