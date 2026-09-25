import React from "react";

type Props = { children: React.ReactNode };
type State = { failed: boolean };

export class AppErrorBoundary extends React.Component<Props, State> {
  state: State = { failed: false };
  static getDerivedStateFromError(): State { return { failed: true }; }
  componentDidCatch(error: Error) { console.error("MDARIX frontend error", error); }
  render() {
    if (!this.state.failed) return this.props.children;
    return <main className="auth-shell" role="alert"><section className="auth-card"><span className="eyebrow">MDARIX secure application</span><h1>Something went wrong</h1><p>The page could not be loaded safely. Refresh the page or return to the home screen.</p><button className="primary-action" onClick={() => window.location.reload()}>Refresh</button></section></main>;
  }
}
