import { redirect } from 'next/navigation';

// Deprecada: el grafo de dependencias era una meta-vista sin decision asociada.
// El mapa de la plataforma cubre la vista de arquitectura.
export default function RedRedirect() {
  redirect('/mapa');
}
