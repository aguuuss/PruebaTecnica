import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import { RefreshCcw, Search, Trash2, Save, Pencil, X, Play } from "lucide-react";
import "./styles.css";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
const IMPORT_TOKEN_STORAGE_KEY = "import-run-token";

type Place = {
  id: number;
  name: string;
  address: string | null;
  city: string | null;
  category: string;
  source: string;
  source_url: string;
  contact: string | null;
  opening_hours: string | null;
  services: string | null;
  description: string | null;
  is_active: boolean;
  fetched_at: string;
  updated_at: string;
};

type ImportLog = {
  id: number;
  status: string;
  items_found: number;
  created_count: number;
  updated_count: number;
  duplicate_count: number;
  error_message: string | null;
  started_at: string;
  finished_at: string | null;
};

type Dashboard = {
  active_places: number;
  inactive_places: number;
  categories: Record<string, number>;
  last_import: ImportLog | null;
};

type Draft = Pick<Place, "name" | "address" | "city" | "category" | "contact" | "opening_hours" | "services" | "description" | "is_active">;

function emptyDraft(): Draft {
  return {
    name: "",
    address: "",
    city: "",
    category: "bar",
    contact: "",
    opening_hours: "",
    services: "",
    description: "",
    is_active: true,
  };
}

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.json();
}

function App() {
  const [places, setPlaces] = useState<Place[]>([]);
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [logs, setLogs] = useState<ImportLog[]>([]);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [importToken, setImportToken] = useState(() => localStorage.getItem(IMPORT_TOKEN_STORAGE_KEY) || "");
  const [editing, setEditing] = useState<number | "new" | null>(null);
  const [draft, setDraft] = useState<Draft>(emptyDraft());

  const filtered = useMemo(() => places, [places]);

  async function load() {
    setError("");
    const search = query ? `?q=${encodeURIComponent(query)}` : "";
    const [placeData, dashboardData, logData] = await Promise.all([
      api<Place[]>(`/places${search}`),
      api<Dashboard>("/dashboard"),
      api<ImportLog[]>("/imports/logs"),
    ]);
    setPlaces(placeData);
    setDashboard(dashboardData);
    setLogs(logData);
  }

  useEffect(() => {
    load().catch((err) => setError(err.message));
  }, []);

  useEffect(() => {
    localStorage.setItem(IMPORT_TOKEN_STORAGE_KEY, importToken);
  }, [importToken]);

  async function runImport() {
    if (!importToken.trim()) {
      setError("Ingresa el token para ejecutar la importacion");
      return;
    }
    setLoading(true);
    setError("");
    try {
      await api<ImportLog>("/imports/run", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${importToken.trim()}`,
        },
      });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error importando datos");
    } finally {
      setLoading(false);
    }
  }

  function startEdit(place: Place) {
    setEditing(place.id);
    setDraft({
      name: place.name,
      address: place.address || "",
      city: place.city || "",
      category: place.category,
      contact: place.contact || "",
      opening_hours: place.opening_hours || "",
      services: place.services || "",
      description: place.description || "",
      is_active: place.is_active,
    });
  }

  function startNew() {
    setEditing("new");
    setDraft(emptyDraft());
  }

  async function save() {
    if (!draft.name.trim()) {
      setError("El nombre es obligatorio");
      return;
    }
    const payload = JSON.stringify(draft);
    if (editing === "new") {
      await api<Place>("/places", { method: "POST", body: payload });
    } else if (typeof editing === "number") {
      await api<Place>(`/places/${editing}`, { method: "PATCH", body: payload });
    }
    setEditing(null);
    setDraft(emptyDraft());
    await load();
  }

  async function deactivate(id: number) {
    await api<Place>(`/places/${id}`, { method: "DELETE" });
    await load();
  }

  return (
    <main className="shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Automatizacion + IA</p>
          <h1>Bares de Tucuman</h1>
        </div>
        <div className="import-controls">
          <input
            type="password"
            value={importToken}
            onChange={(event) => setImportToken(event.target.value)}
            placeholder="Token importacion"
            autoComplete="off"
          />
          <button className="primary" onClick={runImport} disabled={loading}>
            {loading ? <RefreshCcw className="spin" size={18} /> : <Play size={18} />}
            Importar datos
          </button>
        </div>
      </header>

      {dashboard && (
        <section className="metrics">
          <Metric label="Activos" value={dashboard.active_places} />
          <Metric label="Inactivos" value={dashboard.inactive_places} />
          <Metric label="Categorias" value={Object.keys(dashboard.categories).length} />
          <Metric label="Duplicados ultima carga" value={dashboard.last_import?.duplicate_count ?? 0} />
        </section>
      )}

      <section className="workspace">
        <div className="panel main-panel">
          <div className="toolbar">
            <div className="search">
              <Search size={18} />
              <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Buscar por nombre, direccion o ciudad" />
              <button title="Buscar" onClick={() => load().catch((err) => setError(err.message))}>
                <RefreshCcw size={17} />
              </button>
            </div>
            <button onClick={startNew}>
              <Pencil size={17} />
              Nuevo
            </button>
          </div>

          {error && <div className="error">{error}</div>}

          {editing && (
            <Editor draft={draft} setDraft={setDraft} onSave={save} onCancel={() => setEditing(null)} />
          )}

          <div className="table">
            {filtered.map((place) => (
              <article key={place.id} className={`row ${!place.is_active ? "muted" : ""}`}>
                <div>
                  <strong>{place.name}</strong>
                  <p>{place.address || "Sin direccion"} {place.city ? `- ${place.city}` : ""}</p>
                  <small>{place.description || "Sin descripcion"}</small>
                </div>
                <span className="badge">{place.category}</span>
                <span>{new Date(place.fetched_at).toLocaleDateString()}</span>
                <div className="actions">
                  <button title="Editar" onClick={() => startEdit(place)}><Pencil size={16} /></button>
                  <button title="Desactivar" onClick={() => deactivate(place.id)}><Trash2 size={16} /></button>
                </div>
              </article>
            ))}
            {filtered.length === 0 && <div className="empty">Todavia no hay registros. Ejecuta la importacion para cargar datos.</div>}
          </div>
        </div>

        <aside className="panel side-panel">
          <h2>Ultimas cargas</h2>
          {logs.map((log) => (
            <div key={log.id} className="log">
              <strong>{log.status}</strong>
              <span>{new Date(log.started_at).toLocaleString()}</span>
              <p>{log.items_found} encontrados · {log.created_count} nuevos · {log.updated_count} actualizados</p>
              {log.error_message && <small>{log.error_message}</small>}
            </div>
          ))}
        </aside>
      </section>
    </main>
  );
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function Editor({ draft, setDraft, onSave, onCancel }: { draft: Draft; setDraft: (draft: Draft) => void; onSave: () => void; onCancel: () => void }) {
  const update = (key: keyof Draft, value: string | boolean) => setDraft({ ...draft, [key]: value });
  return (
    <div className="editor">
      <input value={draft.name} onChange={(event) => update("name", event.target.value)} placeholder="Nombre" />
      <input value={draft.address || ""} onChange={(event) => update("address", event.target.value)} placeholder="Direccion" />
      <input value={draft.city || ""} onChange={(event) => update("city", event.target.value)} placeholder="Ciudad" />
      <select value={draft.category} onChange={(event) => update("category", event.target.value)}>
        <option value="bar">Bar</option>
        <option value="restaurante">Restaurante</option>
        <option value="cafe">Cafe</option>
        <option value="pizzeria">Pizzeria</option>
        <option value="heladeria">Heladeria</option>
        <option value="regional">Regional</option>
        <option value="otro">Otro</option>
      </select>
      <input value={draft.contact || ""} onChange={(event) => update("contact", event.target.value)} placeholder="Contacto" />
      <textarea value={draft.description || ""} onChange={(event) => update("description", event.target.value)} placeholder="Descripcion" />
      <label className="toggle">
        <input type="checkbox" checked={draft.is_active} onChange={(event) => update("is_active", event.target.checked)} />
        Activo
      </label>
      <div className="editor-actions">
        <button className="primary" onClick={onSave}><Save size={17} /> Guardar</button>
        <button onClick={onCancel}><X size={17} /> Cancelar</button>
      </div>
    </div>
  );
}

createRoot(document.getElementById("root")!).render(<App />);
