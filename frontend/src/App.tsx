import React, { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000';

interface Activity {
  id: string;
  user_id: string;
  external_id: string;
  source: string;
  start_time: string;
  duration_seconds: number;
  distance_meters: number;
  avg_heart_rate?: number | null;
}

interface Insight {
  id: string;
  activity_id: string;
  status: string;
  summary?: string | null;
  created_at: string;
}

async function fetchActivities(): Promise<Activity[]> {
  const res = await fetch(`${API_BASE}/activities/`);
  if (!res.ok) throw new Error('Failed to fetch activities');
  return res.json();
}

async function fetchNearby(lat: number, lon: number, radius_meters: number): Promise<Activity[]> {
  const params = new URLSearchParams({ lat: String(lat), lon: String(lon), radius_meters: String(radius_meters) });
  const res = await fetch(`${API_BASE}/activities/nearby?${params.toString()}`);
  if (!res.ok) throw new Error('Failed to fetch nearby activities');
  return res.json();
}

async function createInsight(activityId: string): Promise<Insight> {
  const res = await fetch(`${API_BASE}/activities/${activityId}/generate-insight`, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to create insight');
  return res.json();
}

async function fetchInsight(id: string): Promise<Insight> {
  const res = await fetch(`${API_BASE}/insights/${id}`);
  if (!res.ok) throw new Error('Failed to fetch insight');
  return res.json();
}

async function importStravaActivities(athleteId?: number, perPage = 10): Promise<{ imported: number }> {
  const res = await fetch(`${API_BASE}/strava/import-activities`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ athlete_id: athleteId, per_page: perPage }),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || 'Failed to import Strava activities');
  }
  return res.json();
}

async function exchangeStravaCode(code: string): Promise<{ athlete_id: number }> {
  const res = await fetch(`${API_BASE}/strava/oauth/exchange`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ code }),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || 'Failed to exchange Strava code');
  }
  return res.json();
}

const App: React.FC = () => {
  const queryClient = useQueryClient();
  const [nearbyParams, setNearbyParams] = useState({ lat: 47.3769, lon: 8.5417, radius_meters: 1000 });
  const [selectedInsightId, setSelectedInsightId] = useState<string | null>(null);
  const [authCode, setAuthCode] = useState('');

  const activitiesQuery = useQuery({ queryKey: ['activities'], queryFn: fetchActivities });

  const nearbyQuery = useQuery({
    queryKey: ['nearby', nearbyParams],
    queryFn: () => fetchNearby(nearbyParams.lat, nearbyParams.lon, nearbyParams.radius_meters),
  });

  const importMutation = useMutation({
    mutationFn: () => importStravaActivities(undefined, 10),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['activities'] });
    },
  });

  const exchangeMutation = useMutation({
    mutationFn: () => exchangeStravaCode(authCode),
    onSuccess: (data) => {
      setAuthCode('');
      // Optionally refresh activities after a successful import later
    },
  });

  const insightMutation = useMutation({
    mutationFn: createInsight,
    onSuccess: (data) => {
      setSelectedInsightId(data.id);
    },
  });

  const insightQuery = useQuery({
    queryKey: ['insight', selectedInsightId],
    queryFn: () => fetchInsight(selectedInsightId as string),
    enabled: !!selectedInsightId,
    refetchInterval: (data) => {
      if (!data) return 3000;
      return data.status === 'done' || data.status === 'failed' ? false : 3000;
    },
  });

  return (
    <div style={{ maxWidth: 960, margin: '0 auto', padding: '1.5rem', fontFamily: 'system-ui, sans-serif' }}>
      <h1>Geo Activity Insights</h1>

      <section style={{ marginBottom: '1.5rem' }}>
        <h2>Seed from Strava</h2>
        <p style={{ maxWidth: 640 }}>
          Connect your Strava account and import recent activities. The flow is:
        </p>
        <ol style={{ maxWidth: 640, lineHeight: 1.6 }}>
          <li>
            <a
              href="https://www.strava.com/oauth/authorize?client_id=199669&response_type=code&redirect_uri=http://localhost:8000/strava/oauth/callback&scope=activity:read_all&approval_prompt=force"
              target="_blank"
              rel="noopener noreferrer"
            >
              Authorize with Strava
            </a>{' '}
            → you’ll land on a page showing a <strong>code</strong>.
          </li>
          <li>Paste the code below and click <strong>Exchange code</strong>.</li>
          <li>Click <strong>Import recent Strava activities</strong>.</li>
        </ol>

        <div style={{ marginTop: '1rem' }}>
          <input
            type="text"
            placeholder="Paste Strava authorization code here"
            value={authCode}
            onChange={(e) => setAuthCode(e.target.value)}
            style={{ width: '100%', maxWidth: 500, padding: '0.5rem', marginBottom: '0.5rem' }}
          />
          <br />
          <button onClick={() => exchangeMutation.mutate()} disabled={!authCode.trim() || exchangeMutation.isPending}>
            {exchangeMutation.isPending ? 'Exchanging…' : 'Exchange code'}
          </button>
          {exchangeMutation.data && (
            <p style={{ marginTop: '0.5rem' }}>
              ✅ Tokens saved for athlete_id {exchangeMutation.data.athlete_id}. You can now import activities.
            </p>
          )}
          {exchangeMutation.error && (
            <p style={{ marginTop: '0.5rem', color: 'red' }}>
              Exchange error: {(exchangeMutation.error as Error).message}
            </p>
          )}
        </div>

        <div style={{ marginTop: '1.5rem' }}>
          <button onClick={() => importMutation.mutate()} disabled={importMutation.isPending}>
            {importMutation.isPending ? 'Importing…' : 'Import recent Strava activities'}
          </button>
          {importMutation.data && (
            <p style={{ marginTop: '0.5rem' }}>
              Imported {importMutation.data.imported} activities from Strava.
            </p>
          )}
          {importMutation.error && (
            <p style={{ marginTop: '0.5rem', color: 'red' }}>
              Import error: {(importMutation.error as Error).message}
            </p>
          )}
        </div>
      </section>

      <section style={{ marginBottom: '2rem' }}>
        <h2>Activity Dashboard</h2>
        {activitiesQuery.isLoading && <p>Loading activities...</p>}
        {activitiesQuery.error && (
          <p>
            Error loading activities: {(activitiesQuery.error as Error).message}
          </p>
        )}
        {activitiesQuery.data && (
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr>
                <th align="left">Start</th>
                <th align="left">Source</th>
                <th align="right">Distance (km)</th>
                <th align="right">Duration (min)</th>
                <th align="right">Avg HR</th>
                <th align="left">Insight</th>
              </tr>
            </thead>
            <tbody>
              {activitiesQuery.data.map((a) => (
                <tr key={a.id}>
                  <td>{new Date(a.start_time).toLocaleString()}</td>
                  <td>{a.source}</td>
                  <td align="right">{(a.distance_meters / 1000).toFixed(1)}</td>
                  <td align="right">{(a.duration_seconds / 60).toFixed(0)}</td>
                  <td align="right">{a.avg_heart_rate ?? '-'}</td>
                  <td>
                    <button onClick={() => insightMutation.mutate(a.id)} disabled={insightMutation.isPending}>
                      Generate Insight
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      <section style={{ marginBottom: '2rem' }}>
        <h2>Nearby Search</h2>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            queryClient.invalidateQueries({ queryKey: ['nearby'] });
          }}
          style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', alignItems: 'flex-end' }}
        >
          <label>
            Lat
            <input
              type="number"
              step="0.0001"
              value={nearbyParams.lat}
              onChange={(e) => setNearbyParams((p) => ({ ...p, lat: Number(e.target.value) }))}
            />
          </label>
          <label>
            Lon
            <input
              type="number"
              step="0.0001"
              value={nearbyParams.lon}
              onChange={(e) => setNearbyParams((p) => ({ ...p, lon: Number(e.target.value) }))}
            />
          </label>
          <label>
            Radius (m)
            <input
              type="number"
              value={nearbyParams.radius_meters}
              onChange={(e) => setNearbyParams((p) => ({ ...p, radius_meters: Number(e.target.value) }))}
            />
          </label>
          <button type="submit">Search</button>
        </form>
        {nearbyQuery.isLoading && <p>Searching...</p>}
        {nearbyQuery.error && (
          <p>
            Error searching nearby activities: {(nearbyQuery.error as Error).message}
          </p>
        )}
        {nearbyQuery.data && <p>Found {nearbyQuery.data.length} activities within radius.</p>}
      </section>

      <section>
        <h2>Insight Viewer</h2>
        {!selectedInsightId && <p>No insight requested yet.</p>}
        {selectedInsightId && insightQuery.isLoading && <p>Loading insight...</p>}
        {selectedInsightId && insightQuery.data && (
          <div>
            <p>
              Status: <strong>{insightQuery.data.status}</strong>
            </p>
            {insightQuery.data.summary && (
              <p>
                <strong>Summary:</strong> {insightQuery.data.summary}
              </p>
            )}
          </div>
        )}
      </section>
    </div>
  );
};

export default App;
