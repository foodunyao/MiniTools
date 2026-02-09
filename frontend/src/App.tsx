import { useState } from "react";
import "./App.css";
import Header from "./Header";

function App() {
  const [count, setCount] = useState(0);
  const [showSidebar, setShowSidebar] = useState(false);

  const toggleSidebar = () => {
    if (showSidebar) {
      setShowSidebar(false);
    } else {
      setShowSidebar(true);
    }
  };

  return (
    <>
      <Header toggleSidebar={toggleSidebar}></Header>
      {showSidebar ? <p>SIDEBARSHOWN</p> : <p>SIDEBARHIDDEN</p>}
      <p>{count}</p>
      <button onClick={() => setCount((prev) => (prev += 1))}>Increment</button>
    </>
  );
}

export default App;
