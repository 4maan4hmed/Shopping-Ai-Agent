import { useState, useEffect } from "react";

const API = "http://localhost:8000";

function api(path, opts = {}, token) {
  return fetch(`${API}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    ...opts,
  }).then((r) => r.json());
}

// ── tiny shared styles ──────────────────────────────────────────────────────
const S = {
  page: {
    fontFamily: "'DM Mono', monospace",
    background: "#f7f5f0",
    minHeight: "100vh",
    color: "#1a1a1a",
    padding: "0 0 60px",
  },
  header: {
    background: "#1a1a1a",
    color: "#f7f5f0",
    padding: "14px 28px",
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
  },
  logo: { fontSize: 16, letterSpacing: 4, fontWeight: 700, margin: 0 },
  nav: { display: "flex", gap: 8 },
  navBtn: (active) => ({
    background: active ? "#f7f5f0" : "transparent",
    color: active ? "#1a1a1a" : "#f7f5f0",
    border: "1px solid #f7f5f0",
    padding: "5px 14px",
    cursor: "pointer",
    fontSize: 12,
    letterSpacing: 1,
  }),
  container: { maxWidth: 720, margin: "0 auto", padding: "32px 20px" },
  card: {
    background: "#fff",
    border: "1px solid #e0ddd6",
    padding: 20,
    marginBottom: 16,
  },
  input: {
    width: "100%",
    border: "1px solid #ccc",
    padding: "8px 10px",
    fontSize: 13,
    fontFamily: "inherit",
    background: "#fafafa",
    boxSizing: "border-box",
    marginBottom: 10,
  },
  btn: (variant = "primary") => ({
    background: variant === "primary" ? "#1a1a1a" : "#fff",
    color: variant === "primary" ? "#f7f5f0" : "#1a1a1a",
    border: "1px solid #1a1a1a",
    padding: "8px 18px",
    cursor: "pointer",
    fontSize: 12,
    letterSpacing: 1,
    fontFamily: "inherit",
  }),
  tag: (color = "#e8e4dc") => ({
    background: color,
    padding: "2px 8px",
    fontSize: 11,
    marginRight: 4,
    letterSpacing: 0.5,
  }),
  msg: (type) => ({
    padding: "10px 14px",
    marginBottom: 12,
    fontSize: 12,
    background: type === "error" ? "#fde8e8" : "#e8f5e9",
    border: `1px solid ${type === "error" ? "#f5c6c6" : "#c3e6cb"}`,
  }),
};

// ── Auth ────────────────────────────────────────────────────────────────────
function AuthPanel({ onLogin }) {
  const [mode, setMode] = useState("login");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [msg, setMsg] = useState(null);

  async function submit() {
    setMsg(null);
    const endpoint = mode === "login" ? "/api/auth/login" : "/api/auth/register";
    const res = await api(endpoint, {
      method: "POST",
      body: JSON.stringify({ username, password }),
    });
    if (res.access_token) {
      onLogin(res.access_token, username);
    } else {
      setMsg({ type: "error", text: res.detail || "Something went wrong" });
    }
  }

  return (
    <div style={S.container}>
      <div style={S.card}>
        <div style={{ display: "flex", gap: 8, marginBottom: 20 }}>
          {["login", "register"].map((m) => (
            <button key={m} style={S.btn(mode === m ? "primary" : "secondary")} onClick={() => setMode(m)}>
              {m.toUpperCase()}
            </button>
          ))}
        </div>
        {msg && <div style={S.msg(msg.type)}>{msg.text}</div>}
        <input style={S.input} placeholder="username" value={username} onChange={(e) => setUsername(e.target.value)} />
        <input
          style={S.input}
          placeholder="password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && submit()}
        />
        <button style={S.btn()} onClick={submit}>
          {mode === "login" ? "SIGN IN" : "CREATE ACCOUNT"}
        </button>
      </div>
    </div>
  );
}

// ── Chat ────────────────────────────────────────────────────────────────────
function ChatPanel({ token }) {
  const [messages, setMessages] = useState([{ role: "assistant", text: "Hi! Ask me anything about products or your orders." }]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  async function send() {
    if (!input.trim()) return;
    const userMsg = input.trim();
    setInput("");
    setMessages((m) => [...m, { role: "user", text: userMsg }]);
    setLoading(true);
    const res = await api("/api/chat", { method: "POST", body: JSON.stringify({ message: userMsg }) }, token);
    setLoading(false);
    setMessages((m) => [...m, { role: "assistant", text: res.response || res.detail || JSON.stringify(res) }]);
  }

  return (
    <div style={S.container}>
      <div style={{ ...S.card, padding: 0, overflow: "hidden" }}>
        <div style={{ background: "#1a1a1a", color: "#f7f5f0", padding: "10px 16px", fontSize: 11, letterSpacing: 2 }}>
          AI ASSISTANT
        </div>
        <div style={{ height: 360, overflowY: "auto", padding: 16 }}>
          {messages.map((m, i) => (
            <div key={i} style={{ marginBottom: 12, textAlign: m.role === "user" ? "right" : "left" }}>
              <span
                style={{
                  display: "inline-block",
                  padding: "8px 12px",
                  background: m.role === "user" ? "#1a1a1a" : "#f0ede6",
                  color: m.role === "user" ? "#f7f5f0" : "#1a1a1a",
                  fontSize: 13,
                  maxWidth: "80%",
                }}
              >
                {m.text}
              </span>
            </div>
          ))}
          {loading && <div style={{ color: "#999", fontSize: 12 }}>typing…</div>}
        </div>
        <div style={{ display: "flex", borderTop: "1px solid #e0ddd6" }}>
          <input
            style={{ ...S.input, margin: 0, border: "none", borderRadius: 0, flex: 1 }}
            placeholder="Ask about products, cart, orders…"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && send()}
          />
          <button style={{ ...S.btn(), border: "none", borderLeft: "1px solid #e0ddd6" }} onClick={send}>
            SEND
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Products ────────────────────────────────────────────────────────────────
function ProductsPanel({ token }) {
  const [query, setQuery] = useState("");
  const [maxPrice, setMaxPrice] = useState("");
  const [organic, setOrganic] = useState("");
  const [results, setResults] = useState([]);
  const [msg, setMsg] = useState(null);

  async function search() {
    setMsg(null);
    const res = await api("/api/products/search", {
      method: "POST",
      body: JSON.stringify({
        query,
        max_price: maxPrice ? parseFloat(maxPrice) : null,
        is_organic: organic === "" ? null : organic === "true",
      }),
    });
    setResults(res.products || []);
    if (!res.products?.length) setMsg({ type: "info", text: "No products found." });
  }

  async function addToCart(id) {
    const res = await api("/api/cart/items", { method: "POST", body: JSON.stringify({ product_id: id, quantity: 1 }) }, token);
    setMsg({ type: res.detail ? "error" : "ok", text: res.detail || "Added to cart!" });
  }

  return (
    <div style={S.container}>
      <div style={S.card}>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          <input style={{ ...S.input, marginBottom: 0, flex: 2, minWidth: 140 }} placeholder="Search products…" value={query} onChange={(e) => setQuery(e.target.value)} onKeyDown={(e) => e.key === "Enter" && search()} />
          <input style={{ ...S.input, marginBottom: 0, width: 90 }} placeholder="Max $" value={maxPrice} onChange={(e) => setMaxPrice(e.target.value)} />
          <select style={{ ...S.input, marginBottom: 0, width: 110 }} value={organic} onChange={(e) => setOrganic(e.target.value)}>
            <option value="">Any</option>
            <option value="true">Organic</option>
            <option value="false">Non-organic</option>
          </select>
          <button style={S.btn()} onClick={search}>SEARCH</button>
        </div>
      </div>
      {msg && <div style={S.msg(msg.type === "ok" ? "ok" : "error")}>{msg.text}</div>}
      {results.map((p) => (
        <div key={p.id} style={{ ...S.card, display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
          <div>
            <div style={{ fontWeight: 700, marginBottom: 4 }}>{p.name}</div>
            <div style={{ fontSize: 12, color: "#666", marginBottom: 6 }}>{p.description}</div>
            <span style={S.tag()}>${p.price?.toFixed(2)}</span>
            {p.is_organic && <span style={S.tag("#d4edda")}>ORGANIC</span>}
            {p.category && <span style={S.tag("#dde3f0")}>{p.category}</span>}
          </div>
          {token && (
            <button style={{ ...S.btn(), flexShrink: 0 }} onClick={() => addToCart(p.id)}>
              + CART
            </button>
          )}
        </div>
      ))}
    </div>
  );
}

// ── Cart ────────────────────────────────────────────────────────────────────
function CartPanel({ token }) {
  const [cart, setCart] = useState(null);
  const [msg, setMsg] = useState(null);

  async function load() {
    const res = await api("/api/cart", {}, token);
    setCart(res);
  }

  async function remove(id) {
    await api(`/api/cart/items/${id}`, { method: "DELETE" }, token);
    load();
  }

  async function clear() {
    await api("/api/cart", { method: "DELETE" }, token);
    load();
  }

  async function doCheckout(id) {
    const res = await api("/api/checkout", { method: "POST", body: JSON.stringify({ product_id: id }) }, token);
    setMsg({ type: res.detail ? "error" : "ok", text: res.detail || "Order placed!" });
    load();
  }

  useEffect(() => { load(); }, []);

  const items = cart?.items || [];

  return (
    <div style={S.container}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <span style={{ fontSize: 11, letterSpacing: 2 }}>CART ({items.length} items)</span>
        {items.length > 0 && <button style={S.btn("secondary")} onClick={clear}>CLEAR ALL</button>}
      </div>
      {msg && <div style={S.msg(msg.type === "ok" ? "ok" : "error")}>{msg.text}</div>}
      {items.length === 0 && <div style={{ ...S.card, color: "#888", fontSize: 13 }}>Cart is empty.</div>}
      {items.map((item) => (
        <div key={item.product_id} style={{ ...S.card, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div>
            <div style={{ fontWeight: 700, marginBottom: 2 }}>{item.name}</div>
            <span style={S.tag()}>${item.price?.toFixed(2)}</span>
            <span style={S.tag("#dde3f0")}>qty: {item.quantity}</span>
          </div>
          <div style={{ display: "flex", gap: 8 }}>
            <button style={S.btn()} onClick={() => doCheckout(item.product_id)}>CHECKOUT</button>
            <button style={S.btn("secondary")} onClick={() => remove(item.product_id)}>REMOVE</button>
          </div>
        </div>
      ))}
    </div>
  );
}

// ── Deliveries ──────────────────────────────────────────────────────────────
function DeliveriesPanel({ token }) {
  const [orders, setOrders] = useState(null);

  useEffect(() => {
    api("/api/deliveries", {}, token).then((r) => setOrders(r.orders || r.deliveries || []));
  }, []);

  return (
    <div style={S.container}>
      <div style={{ fontSize: 11, letterSpacing: 2, marginBottom: 16 }}>YOUR ORDERS</div>
      {orders === null && <div style={S.card}>Loading…</div>}
      {orders?.length === 0 && <div style={{ ...S.card, color: "#888", fontSize: 13 }}>No orders yet.</div>}
      {orders?.map((o, i) => (
        <div key={i} style={S.card}>
          <div style={{ fontWeight: 700, marginBottom: 4 }}>{o.product_name || o.name || `Order #${o.id}`}</div>
          <span style={S.tag()}>${o.price?.toFixed(2) ?? "—"}</span>
          <span style={S.tag(o.status === "delivered" ? "#d4edda" : "#fff3cd")}>{(o.status || "pending").toUpperCase()}</span>
          {o.created_at && <div style={{ fontSize: 11, color: "#999", marginTop: 6 }}>{new Date(o.created_at).toLocaleString()}</div>}
        </div>
      ))}
    </div>
  );
}

// ── Image Search ─────────────────────────────────────────────────────────────
function ImageSearchPanel() {
  const [file, setFile] = useState(null);
  const [caption, setCaption] = useState("");
  const [results, setResults] = useState([]);
  const [msg, setMsg] = useState(null);

  async function submit() {
    if (!file) return;
    setMsg(null);
    const fd = new FormData();
    fd.append("image", file);
    fd.append("caption", caption);
    const res = await fetch(`${API}/api/image-search`, { method: "POST", body: fd }).then((r) => r.json());
    setResults(res.products || []);
    if (!res.products?.length) setMsg({ type: "info", text: "No matches found." });
  }

  return (
    <div style={S.container}>
      <div style={S.card}>
        <input type="file" accept="image/*" onChange={(e) => setFile(e.target.files[0])} style={{ marginBottom: 10, fontSize: 12 }} />
        <input style={S.input} placeholder="Optional caption / hint" value={caption} onChange={(e) => setCaption(e.target.value)} />
        <button style={S.btn()} onClick={submit}>SEARCH BY IMAGE</button>
      </div>
      {msg && <div style={S.msg("error")}>{msg.text}</div>}
      {results.map((p) => (
        <div key={p.id} style={S.card}>
          <div style={{ fontWeight: 700 }}>{p.name}</div>
          <div style={{ fontSize: 12, color: "#666" }}>{p.description}</div>
          <span style={S.tag()}>${p.price?.toFixed(2)}</span>
        </div>
      ))}
    </div>
  );
}

// ── App Shell ────────────────────────────────────────────────────────────────
export default function App() {
  const [token, setToken] = useState(null);
  const [username, setUsername] = useState(null);
  const [tab, setTab] = useState("products");

  function logout() {
    setToken(null);
    setUsername(null);
    setTab("products");
  }

  const tabs = token
    ? ["products", "chat", "cart", "orders", "image-search"]
    : ["products", "image-search"];

  return (
    <div style={S.page}>
      <link href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&display=swap" rel="stylesheet" />
      <header style={S.header}>
        <p style={S.logo}>SHOPAI</p>
        <nav style={S.nav}>
          {tabs.map((t) => (
            <button key={t} style={S.navBtn(tab === t)} onClick={() => setTab(t)}>
              {t.toUpperCase()}
            </button>
          ))}
          {token ? (
            <button style={S.navBtn(false)} onClick={logout}>
              {username?.toUpperCase()} ✕
            </button>
          ) : (
            <button style={S.navBtn(tab === "auth")} onClick={() => setTab("auth")}>
              LOGIN
            </button>
          )}
        </nav>
      </header>

      {tab === "auth" && !token && <AuthPanel onLogin={(t, u) => { setToken(t); setUsername(u); setTab("products"); }} />}
      {tab === "products" && <ProductsPanel token={token} />}
      {tab === "chat" && token && <ChatPanel token={token} />}
      {tab === "cart" && token && <CartPanel token={token} />}
      {tab === "orders" && token && <DeliveriesPanel token={token} />}
      {tab === "image-search" && <ImageSearchPanel />}
    </div>
  );
}