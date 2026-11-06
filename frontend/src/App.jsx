import { useCallback, useEffect, useMemo, useState } from "react";
import axios from "axios";
import {
  Activity, ArrowDownLeft, ArrowLeftRight, ArrowUpRight,
  Bell, CreditCard, LayoutDashboard, LogOut, Plus,
  RefreshCw, ShieldCheck, Wallet
} from "lucide-react";

const api = axios.create({ baseURL: "/api" });

const money = (v) =>
  new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR"
  }).format(Number(v || 0));

const date = (v) => v ? new Date(v).toLocaleString("en-IN") : "—";

export default function App() {
  const [token, setToken] = useState(
    localStorage.getItem("securebank_token") || ""
  );
  const [user, setUser] = useState(null);
  const [accounts, setAccounts] = useState([]);
  const [transactions, setTransactions] = useState([]);
  const [notifications, setNotifications] = useState([]);

  const [page, setPage] = useState("overview");
  const [authMode, setAuthMode] = useState("login");
  const [form, setForm] = useState({
    username: "", email: "", password: ""
  });

  const [modal, setModal] = useState("");
  const [accountType, setAccountType] = useState("SAVINGS");
  const [tx, setTx] = useState({
    account_id: "",
    from_account_id: "",
    to_account_id: "",
    amount: ""
  });

  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);

  const request = useCallback((config) => api({
    ...config,
    headers: {
      ...config.headers,
      Authorization: `Bearer ${token}`
    }
  }), [token]);

  const loadData = useCallback(async () => {
    if (!token) return;

    setBusy(true);
    setError("");

    try {
      const [u, a, t, n] = await Promise.all([
        request({ url: "/v1/auth/me" }),
        request({ url: "/v1/accounts" }),
        request({ url: "/v1/transactions" }),
        request({ url: "/v1/notifications" })
      ]);

      setUser(u.data);
      setAccounts(a.data);
      setTransactions(t.data);
      setNotifications(n.data);

      setTx(old => ({
        ...old,
        account_id: old.account_id || String(a.data[0]?.id || ""),
        from_account_id: old.from_account_id || String(a.data[0]?.id || ""),
        to_account_id: old.to_account_id || String(a.data[1]?.id || "")
      }));
    } catch (e) {
      setError(e.response?.data?.detail || "Unable to load dashboard.");

      if (e.response?.status === 401) {
        localStorage.removeItem("securebank_token");
        setToken("");
      }
    } finally {
      setBusy(false);
    }
  }, [token, request]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const totalBalance = useMemo(
    () => accounts.reduce((sum, a) => sum + Number(a.balance || 0), 0),
    [accounts]
  );

  async function authenticate(e) {
    e.preventDefault();
    setBusy(true);
    setError("");

    try {
      if (authMode === "register") {
        await api.post("/v1/auth/register", form);
        setMessage("Registration successful. Please sign in.");
        setAuthMode("login");
      } else {
        const result = await api.post("/v1/auth/login", {
          username: form.username,
          password: form.password
        });

        localStorage.setItem(
          "securebank_token",
          result.data.access_token
        );
        setToken(result.data.access_token);
      }
    } catch (e) {
      setError(e.response?.data?.detail || "Authentication failed.");
    } finally {
      setBusy(false);
    }
  }

  function logout() {
    localStorage.removeItem("securebank_token");
    setToken("");
    setUser(null);
    setAccounts([]);
    setTransactions([]);
    setNotifications([]);
  }

  async function createAccount(e) {
    e.preventDefault();
    setBusy(true);
    setError("");

    try {
      await request({
        method: "POST",
        url: "/v1/accounts",
        data: { account_type: accountType }
      });

      setMessage("Account created successfully.");
      setModal("");
      await loadData();
    } catch (e) {
      setError(e.response?.data?.detail || "Account creation failed.");
    } finally {
      setBusy(false);
    }
  }

  async function submitTransaction(e) {
    e.preventDefault();
    setBusy(true);
    setError("");

    const data = { amount: String(tx.amount) };
    let url = `/v1/transactions/${modal}`;

    if (modal === "transfer") {
      data.from_account_id = Number(tx.from_account_id);
      data.to_account_id = Number(tx.to_account_id);
    } else {
      data.account_id = Number(tx.account_id);
    }

    try {
      await request({ method: "POST", url, data });

      setMessage("Transaction completed successfully.");
      setModal("");
      setTx(old => ({ ...old, amount: "" }));
      await loadData();
    } catch (e) {
      setError(e.response?.data?.detail || "Transaction failed.");
    } finally {
      setBusy(false);
    }
  }

  if (!token) {
    return (
      <div className="auth-layout">
        <section className="hero">
          <div className="brand"><ShieldCheck /> SecureBank</div>
          <div>
            <small>YOUR MONEY, IN CLEAR VIEW</small>
            <h1>Banking that<br />moves with you.</h1>
            <p>Manage accounts, move money and track every transaction from one dashboard.</p>
          </div>
        </section>

        <section className="auth-panel">
          <form className="auth-card" onSubmit={authenticate}>
            <small className="eyebrow">
              {authMode === "login" ? "WELCOME BACK" : "JOIN SECUREBANK"}
            </small>

            <h2>
              {authMode === "login" ? "Sign in" : "Create account"}
            </h2>

            <label>Username
              <input
                required
                value={form.username}
                onChange={e => setForm({...form, username:e.target.value})}
              />
            </label>

            {authMode === "register" && (
              <label>Email
                <input
                  type="email"
                  required
                  value={form.email}
                  onChange={e => setForm({...form, email:e.target.value})}
                />
              </label>
            )}

            <label>Password
              <input
                type="password"
                required
                minLength={authMode === "register" ? 8 : 1}
                value={form.password}
                onChange={e => setForm({...form, password:e.target.value})}
              />
            </label>

            {error && <p className="error">{error}</p>}
            {message && <p className="success">{message}</p>}

            <button className="primary full" disabled={busy}>
              {busy ? "Please wait..." :
                authMode === "login" ? "Sign in" : "Register"}
            </button>

            <p className="switch">
              {authMode === "login" ? "New customer?" : "Already registered?"}
              <button type="button" onClick={() => {
                setAuthMode(authMode === "login" ? "register" : "login");
                setError("");
              }}>
                {authMode === "login" ? "Create account" : "Sign in"}
              </button>
            </p>
          </form>
        </section>
      </div>
    );
  }

  const navigation = [
    ["overview", "Overview", LayoutDashboard],
    ["accounts", "Accounts", Wallet],
    ["transactions", "Transactions", Activity],
    ["notifications", "Notifications", Bell]
  ];

  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="brand"><ShieldCheck /> SecureBank</div>
        <small className="nav-title">WORKSPACE</small>

        {navigation.map(([id, label, Icon]) => (
          <button
            key={id}
            className={page === id ? "nav active" : "nav"}
            onClick={() => setPage(id)}
          >
            <Icon size={18} />
            {label}
            {id === "notifications" && notifications.length > 0 &&
              <span className="count">{notifications.length}</span>}
          </button>
        ))}

        <div className="sidebar-bottom">
          <div className="secure"><ShieldCheck /> Secure session active</div>
          <button className="nav" onClick={logout}>
            <LogOut size={18}/> Sign out
          </button>
        </div>
      </aside>

      <main>
        <header className="topbar">
          <div>
            <small className="eyebrow">SECUREBANK / CUSTOMER</small>
            <h1>{navigation.find(n => n[0] === page)?.[1]}</h1>
          </div>
          <div className="user">
            <button className="icon" onClick={loadData}><RefreshCw size={17}/></button>
            <span>{user?.username}</span>
          </div>
        </header>

        <div className="content">
          {error && <div className="error">{error}</div>}
          {message && <div className="success">{message}</div>}

          {page === "overview" && <>
            <div className="heading">
              <div><h2>Hello, {user?.username}</h2><p>Your banking snapshot.</p></div>
              <button className="primary" onClick={() => setModal("account")}>
                <Plus size={16}/> Open account
              </button>
            </div>

            <div className="metrics">
              <div className="total">
                <small>TOTAL BALANCE</small>
                <h2>{money(totalBalance)}</h2>
                <p>{accounts.length} account(s)</p>
              </div>
              <div className="metric">
                <CreditCard/><small>ACCOUNTS</small><strong>{accounts.length}</strong>
              </div>
              <div className="metric">
                <Activity/><small>TRANSACTIONS</small><strong>{transactions.length}</strong>
              </div>
            </div>

            <Section title="Your accounts" action="View all" onClick={() => setPage("accounts")}/>
            <AccountCards accounts={accounts.slice(0,3)}/>

            <Section title="Recent transactions" action="View history" onClick={() => setPage("transactions")}/>
            <TransactionTable rows={transactions.slice(0,5)}/>
          </>}

          {page === "accounts" && <>
            <div className="heading">
              <div><h2>Your accounts</h2><p>Manage your bank accounts.</p></div>
              <button className="primary" onClick={() => setModal("account")}><Plus size={16}/> Open account</button>
            </div>
            <AccountCards accounts={accounts}/>
          </>}

          {page === "transactions" && <>
            <div className="heading"><div><h2>Move money</h2><p>Deposit, withdraw or transfer funds.</p></div></div>
            <div className="actions">
              <button onClick={() => setModal("deposit")}><ArrowDownLeft/><b>Deposit</b></button>
              <button onClick={() => setModal("withdraw")}><ArrowUpRight/><b>Withdraw</b></button>
              <button onClick={() => setModal("transfer")}><ArrowLeftRight/><b>Transfer</b></button>
            </div>
            <Section title="Transaction history"/>
            <TransactionTable rows={transactions}/>
          </>}

          {page === "notifications" && <>
            <div className="heading"><div><h2>Notifications</h2><p>Banking activity updates.</p></div></div>
            {notifications.length ? notifications.map(n => (
              <div className="notification" key={n.id}>
                <Bell/><div><b>{n.event_type}</b><p>{n.message}</p><small>{date(n.created_at)} · {n.status}</small></div>
              </div>
            )) : <Empty>No notifications yet.</Empty>}
          </>}

          <footer>SecureBank · Learning/demo application · Not for real funds</footer>
        </div>
      </main>

      {modal && <div className="shade">
        <form className="dialog" onSubmit={modal === "account" ? createAccount : submitTransaction}>
          <div className="dialog-head">
            <h2>{modal === "account" ? "Open account" : `${modal} funds`}</h2>
            <button type="button" onClick={() => setModal("")}>×</button>
          </div>

          {modal === "account" ? (
            <label>Account type
              <select value={accountType} onChange={e => setAccountType(e.target.value)}>
                <option value="SAVINGS">Savings</option>
                <option value="CURRENT">Current</option>
              </select>
            </label>
          ) : <>
            {modal === "transfer" ? <>
              <label>From account
                <select value={tx.from_account_id} onChange={e => setTx({...tx,from_account_id:e.target.value})}>
                  {accounts.map(a => <option key={a.id} value={a.id}>{a.account_number} · {a.account_type}</option>)}
                </select>
              </label>
              <label>To account
                <select value={tx.to_account_id} onChange={e => setTx({...tx,to_account_id:e.target.value})}>
                  {accounts.map(a => <option key={a.id} value={a.id}>{a.account_number} · {a.account_type}</option>)}
                </select>
              </label>
            </> : <label>Account
              <select value={tx.account_id} onChange={e => setTx({...tx,account_id:e.target.value})}>
                {accounts.map(a => <option key={a.id} value={a.id}>{a.account_number} · {money(a.balance)}</option>)}
              </select>
            </label>}
            <label>Amount (INR)
              <input type="number" min="0.01" step="0.01" required value={tx.amount} onChange={e => setTx({...tx,amount:e.target.value})}/>
            </label>
          </>}

          <button className="primary full" disabled={busy || (!accounts.length && modal !== "account")}>
            {busy ? "Processing..." : "Confirm"}
          </button>
        </form>
      </div>}
    </div>
  );
}

function Section({title,action,onClick}) {
  return <div className="section"><h3>{title}</h3>{action && <button onClick={onClick}>{action}</button>}</div>;
}
function AccountCards({accounts}) {
  if (!accounts.length) return <Empty>No accounts yet. Open your first account.</Empty>;
  return <div className="cards">{accounts.map((a,i) => (
    <div className={`bank-card c${i%3}`} key={a.id}>
      <div className="card-head">{a.account_type} ACCOUNT <CreditCard/></div>
      <p>•••• •••• {a.account_number.slice(-4)}</p>
      <small>Available balance</small>
      <h3>{money(a.balance)}</h3>
      <div className="card-foot"><span>{a.status}</span><span>{a.currency}</span></div>
    </div>
  ))}</div>;
}
function TransactionTable({rows}) {
  if (!rows.length) return <Empty>No transactions recorded yet.</Empty>;
  return <div className="table-box"><table>
    <thead><tr><th>Type</th><th>Reference</th><th>Date</th><th>Amount</th><th>Status</th></tr></thead>
    <tbody>{rows.map(t => <tr key={t.id}>
      <td><b>{t.transaction_type}</b></td><td>{t.reference}</td>
      <td>{date(t.created_at)}</td><td>{money(t.amount)}</td><td>{t.status}</td>
    </tr>)}</tbody>
  </table></div>;
}
function Empty({children}) { return <div className="empty"><Wallet/><p>{children}</p></div>; }
