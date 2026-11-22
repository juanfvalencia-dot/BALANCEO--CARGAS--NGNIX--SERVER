import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '15s', target: 20 }, // Calentamiento: sube a 20 usuarios virtuales
    { duration: '30s', target: 50 }, // Carga sostenida: 50 usuarios concurrentes
    { duration: '15s', target: 0 },  // Enfriamiento: baja a 0 usuarios
  ],
};

export default function () {
  const res = http.get('http://localhost:8080/');
  check(res, {
    'status es 200': (r) => r.status === 200,
  });
  sleep(0.2);
}
