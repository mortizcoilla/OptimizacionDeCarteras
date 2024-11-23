import React, { useEffect, useRef } from "react";
import * as d3 from "d3";

const EfficientFrontierGraph = ({ data }) => {
  const svgRef = useRef();

  useEffect(() => {
    if (!data) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove(); // Limpia el gráfico antes de redibujar

    const width = 600;
    const height = 400;
    const margin = { top: 50, right: 30, bottom: 50, left: 60 };

    // Configuración de escalas
    const x = d3
      .scaleLinear()
      .domain([0, d3.max(data, (d) => d.risk)])
      .range([margin.left, width - margin.right]);

    const y = d3
      .scaleLinear()
      .domain([0, d3.max(data, (d) => d.return)])
      .range([height - margin.bottom, margin.top]);

    // Ejes
    svg
      .append("g")
      .attr("transform", `translate(0,${height - margin.bottom})`)
      .call(d3.axisBottom(x))
      .append("text")
      .attr("x", width / 2)
      .attr("y", 35)
      .attr("fill", "black")
      .text("Riesgo");

    svg
      .append("g")
      .attr("transform", `translate(${margin.left},0)`)
      .call(d3.axisLeft(y))
      .append("text")
      .attr("x", -height / 2)
      .attr("y", -40)
      .attr("fill", "black")
      .attr("transform", "rotate(-90)")
      .text("Rentabilidad");

    // Título
    svg
      .append("text")
      .attr("x", width / 2)
      .attr("y", margin.top / 2)
      .attr("text-anchor", "middle")
      .style("font-size", "16px")
      .text("Frontera Eficiente");

    // Línea de la frontera eficiente
    svg
      .append("path")
      .datum(data)
      .attr("fill", "none")
      .attr("stroke", "#064469") // Azul oscuro de tu paleta
      .attr("stroke-width", 2)
      .attr(
        "d",
        d3
          .line()
          .x((d) => x(d.risk))
          .y((d) => y(d.return))
      );

    // Puntos interactivos
    svg
      .selectAll("circle")
      .data(data)
      .enter()
      .append("circle")
      .attr("cx", (d) => x(d.risk))
      .attr("cy", (d) => y(d.return))
      .attr("r", 5)
      .attr("fill", "#5790ab") // Azul más vivo
      .on("mouseover", function (event, d) {
        d3.select(this).attr("fill", "#f3d77f"); // Amarillo para resaltar
        tooltip.style("visibility", "visible").text(
          `Riesgo: ${d.risk.toFixed(2)}, Rentabilidad: ${d.return.toFixed(2)}`
        );
      })
      .on("mousemove", function (event) {
        tooltip
          .style("top", event.pageY - 10 + "px")
          .style("left", event.pageX + 10 + "px");
      })
      .on("mouseout", function () {
        d3.select(this).attr("fill", "#5790ab"); // Volver al azul original
        tooltip.style("visibility", "hidden");
      });

    // Tooltip
    const tooltip = d3
      .select("body")
      .append("div")
      .style("position", "absolute")
      .style("visibility", "hidden")
      .style("background-color", "#fcfbf9") // Blanco suave
      .style("padding", "5px")
      .style("border-radius", "5px")
      .style("box-shadow", "0px 2px 4px rgba(0,0,0,0.2)")
      .style("font-size", "12px");
  }, [data]);

  return <svg ref={svgRef} width={600} height={400}></svg>;
};

export default EfficientFrontierGraph;
