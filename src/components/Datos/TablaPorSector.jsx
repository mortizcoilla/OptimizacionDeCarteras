import React from "react";

const TablaPorSector = ({ data }) => {
  if (!data || data.length === 0) {
    return <p>No hay datos disponibles.</p>;
  }

  // Ordenar la tabla de mayor a menor por capitalización
  const sortedData = data.sort((a, b) => b.capitalizacion - a.capitalizacion);

  return (
    <div className="chart-column">
      <h2>Acciones por Sector</h2>
      <div className="table-container">
        <table>
          <thead>
            <tr>
              <th>Sector</th>
              <th>Cantidad</th>
              <th>Acciones</th>
              <th>Capitalización (M)</th>
            </tr>
          </thead>
          <tbody>
            {sortedData.map((sector, index) => (
              <tr key={index}>
                <td>{sector.sector}</td>
                <td>{sector.cantidad}</td>
                <td>
                  {sector.acciones
                    .map((accion) => accion.replace(".SN", "")) // Eliminar sufijo .SN
                    .join(", ")}
                </td>
                <td>
                  {new Intl.NumberFormat("es-CL", {
                    style: "currency",
                    currency: "CLP",
                  }).format(sector.capitalizacion / 1e6)}{" "}
                  M
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default TablaPorSector;
