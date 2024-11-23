import React, { useState, useEffect } from "react";
import DataLoader from "./components/DataLoader";
import EfficientFrontierGraph from "./components/EfficientFrontierGraph";

const App = () => {
  const [data, setData] = useState(null);

  useEffect(() => {
    fetch("/data/frontier.json")
      .then((response) => response.json())
      .then((json) => setData(json));
  }, []);

  return (
    <div>
      <h1>Optimización de Carteras</h1>
      <EfficientFrontierGraph data={data?.frontier} />
    </div>
  );
};

export default App;
