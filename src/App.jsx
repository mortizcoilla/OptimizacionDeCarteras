import React, { useState, useEffect } from "react";
import EfficientFrontierGraph from "./components/EfficientFrontierGraph";

const App = () => {
  const [data, setData] = useState(null);

  useEffect(() => {
    // Cargar los datos desde la nueva ubicación en /public/data/frontier.json
    fetch("/data/frontier.json")
      .then((response) => {
        if (!response.ok) {
          throw new Error("No se pudieron cargar los datos");
        }
        return response.json();
      })
      .then((json) => setData(json.frontier)) // Asume que el archivo tiene un objeto con "frontier"
      .catch((error) => console.error("Error cargando los datos:", error));
  }, []);

  return (
    <div>
      <h1>Optimización de Carteras</h1>
      {/* Renderizar el gráfico solo si los datos están disponibles */}
      {data ? (
        <EfficientFrontierGraph data={data} />
      ) : (
        <p>Cargando datos...</p>
      )}
    </div>
  );
};

export default App;
