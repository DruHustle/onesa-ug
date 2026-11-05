import React, { Suspense, lazy } from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./styles.css";

const InternalApp = lazy(() => import("./internal/InternalApp"));
const isInternalPreview = window.location.pathname === '/internal' || window.location.pathname.startsWith('/internal/');

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <Suspense fallback={<p style={{padding:24}}>Opening Onesa Mobile…</p>}>
      {isInternalPreview ? <InternalApp /> : <App />}
    </Suspense>
  </React.StrictMode>,
);
