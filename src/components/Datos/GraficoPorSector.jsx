import React, { useEffect, useRef } from "react";
import * as d3 from "d3";

const GraficoPorSector = ({ data, onDrilldown }) => {
  const svgRef = useRef();

  useEffect(() => {
    if (data && data.length > 0) {
      const svg = d3.select(svgRef.current);
      svg.selectAll("*").remove(); // Limpiar el gráfico previo

      const containerWidth = svg.node().parentNode.clientWidth; // Ancho del contenedor
      const margin = { top: 30, right: 40, bottom: 80, left: 120 };
      const width = containerWidth - margin.left - margin.right;
      const height = 400;

      svg.attr("viewBox", `0 0 ${containerWidth} ${height + margin.top + margin.bottom}`)
        .attr("preserveAspectRatio", "xMinYMin meet");

      // Calcular el total de la capitalización
      const total = d3.sum(data, (d) => d.value);

      // Calcular los porcentajes
      const percentageData = data.map((d) => ({
        name: d.name,
        percentage: (d.value / total) * 100,
      }));

      // Ordenar los datos de mayor a menor por porcentaje
      percentageData.sort((a, b) => b.percentage - a.percentage);

      // Escalas para porcentajes
      const x = d3
        .scaleLinear()
        .domain([0, d3.max(percentageData, (d) => d.percentage)])
        .range([0, width]);

      const y = d3
        .scaleBand()
        .domain(percentageData.map((d) => d.name))
        .range([0, height])
        .padding(0.1);

      const g = svg
        .append("g")
        .attr("transform", `translate(${margin.left},${margin.top})`);

      // Dibujar barras
      g.append("g")
        .selectAll("rect")
        .data(percentageData)
        .enter()
        .append("rect")
        .attr("y", (d) => y(d.name))
        .attr("width", (d) => x(d.percentage))
        .attr("height", y.bandwidth())
        .attr("fill", "#02457a")
        .on("click", (event, d) => onDrilldown(d.name));

      // Etiquetas sobre las barras
      g.append("g")
        .selectAll("text")
        .data(percentageData)
        .enter()
        .append("text")
        .attr("y", (d) => y(d.name) + y.bandwidth() / 2)
        .attr("x", (d) => x(d.percentage) + 5) // Etiqueta fuera de la barra
        .attr("dy", ".35em")
        .attr("fill", "#02457a")
        .style("font-size", "12px")
        .text((d) => `${d.percentage.toFixed(2)}%`);

      // Eje Y con nombres de sectores
      g.append("g").call(d3.axisLeft(y));

      // Eje X con porcentajes
      g.append("g")
        .call(d3.axisBottom(x).ticks(5).tickFormat((d) => `${d}%`))
        .attr("transform", `translate(0,${height})`);

      // Título del eje X
      svg
        .append("text")
        .attr("text-anchor", "middle")
        .attr(
          "transform",
          `translate(${margin.left + width / 2}, ${margin.top + height + 40})`
        )
        .text("Porcentaje de Capitalización (%)")
        .attr("fill", "#064469")
        .style("font-size", "14px");
    }
  }, [data, onDrilldown]);

  return (
    <div className="chart-column">
      <h2>Distribución de Capitalización por Sector (%)</h2>
      <svg ref={svgRef} width="100%" height="400"></svg>
    </div>
  );
};

export default GraficoPorSector;
