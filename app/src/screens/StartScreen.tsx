import { useCabinetOrThrow } from "../journey/Cabinet";
import "../practice/practice.css";

export function StartScreen() {
  const { dispatch, emit } = useCabinetOrThrow();
  return (
    <section className="play-shell" aria-labelledby="start-title">
      <header className="play-topline"><span>EV<span className="play-red">GAMEPAD</span></span><span>DEMO ACCOUNTS ONLY</span></header>
      <div className="play-intro">
        <p className="play-eyebrow">YOUR PRACTICE DESK</p>
        <h1 id="start-title">Get comfortable.<br />One decision at a time.</h1>
        <p>Learn the controls, practise changing your mind, and review what you did well. There is no timer and no profit target.</p>
      </div>
      <div className="play-options">
        <section className="play-panel play-feature">
          <p className="play-eyebrow">01 / START HERE</p>
          <h2>Learn the controls</h2>
          <p>A short guided lesson: unlock, cancel, confirm, close, and sit out.</p>
          <p className="play-muted">Use a mouse, keyboard, or controller. No account or token needed. Nothing is sent to a broker.</p>
          <button className="play-primary" onClick={() => emit("start")}>Start practice <span>↗</span></button>
          <small>Enter or controller Start also begins the lesson.</small>
        </section>
        <section className="play-panel">
          <p className="play-eyebrow">02 / WHEN YOU FEEL COMFORTABLE</p>
          <h2>Use your demo account</h2>
          <p>Connect your configured cTrader demo account to practise with market prices and demo funds.</p>
          <p className="play-muted">You need the running gateway, its session token, and a controller for entries.</p>
          <button onClick={() => dispatch({ type: "warp", screen: "live" })}>Open demo desk <span>↗</span></button>
          <small>The desk starts locked. Connecting does not place an order.</small>
        </section>
      </div>
      <section className="play-principle"><strong>A good session can have zero trades.</strong><p>Pick one thing to practise. Stop when you need a break. Confidence comes from knowing what your controls do and following your own plan.</p></section>
      <footer className="play-actions">
        <button onClick={() => dispatch({ type: "warp", screen: "journallive" })}>Review my journal</button>
        <button onClick={() => emit("menu")}>All screens</button>
        <span className="play-muted">Practice results do not predict trading results.</span>
      </footer>
    </section>
  );
}
