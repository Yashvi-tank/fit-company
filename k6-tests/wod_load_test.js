import http from 'k6/http';
import { check, sleep } from 'k6';

export let options = {
  stages: [
    { duration: '10s', target: 10 },   // ramp-up to 10 users
    { duration: '30s', target: 10 },   // hold at 10 users
    { duration: '10s', target: 0 },    // ramp-down to 0
  ],
};

const BASE_URL = 'http://localhost:5000';
const TOKEN = 'PASTE_YOUR_JWT_TOKEN_HERE';  // <--- VERY IMPORTANT

export default function () {
  const res = http.get(`${BASE_URL}/fitness/wod`, {
    headers: {
      Authorization: `Bearer ${TOKEN}`,
    },
  });

  check(res, {
    'status is 200': (r) => r.status === 200,
    'returns JSON': (r) => r.headers['Content-Type'].includes('application/json'),
  });

  sleep(1);  // wait before next iteration
}
