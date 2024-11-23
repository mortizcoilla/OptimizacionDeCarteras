import React, { useEffect, useState } from "react";

const DataLoader = () => {
  const [data, setData] = useState(null);

  useEffect(() => {
    // Cambia la ruta al archivo JSON en tu carpeta data
    fetch("/data/frontier.json")
      .then((response) => response.json())
      .then((json) => setData(json))
      .catch((error) => console.error("Error al cargar los datos:", error));
  }, []);

  return (
    <div>
      <h1>Datos de la Frontera Eficiente</h1>
      {data ? (
        <pre>{JSON.stringify(data, null, 2)}</pre>
      ) : (
        <p>Cargando datos...</p>
      )}
    </div>
  );
};

export default DataLoader;
