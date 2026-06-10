import { redirect } from 'next/navigation';

// Deprecada: era una checklist estatica sin persistencia que duplicaba la
// matriz canonica dinamica. La fuente unica de datos faltantes es /variables.
export default function DatosRedirect() {
  redirect('/variables');
}
