import React, { useEffect, useState } from "react";
import "./Datos.css";
import * as d3 from "d3";
import TablaPorSector from "./TablaPorSector";
import GraficoPorSector from "./GraficoPorSector";

const Datos = () => {
  const [ipsaData, setIpsaData] = useState([]);
  const [loading, setLoading] = useState(true);

  // Cargar datos desde ipsa.csv
  useEffect(() => {
    const fetchData = async () => {
      try {
        const data = await d3.csv("/src/assets/data/ipsa.csv", (d) => ({
          Ticker: d.Ticker,
          NombreCompleto: d["Nombre completo"],
          Sector: d.Sector,
          Industria: d.Industria,
          Capitalizacion: parseFloat(d["Capitalización de mercado"] || 0),
        }));
        setIpsaData(data);
        setLoading(false);
      } catch (error) {
        console.error("Error al cargar los datos de IPSA:", error);
      }
    };
    fetchData();
  }, []);

  // Obtener datos agrupados por sector
  const getActionsBySector = () => {
    return Array.from(
      d3.group(ipsaData, (d) => d.Sector),
      ([sector, acciones]) => ({
        sector,
        cantidad: acciones.length,
        capitalizacion: d3.sum(acciones, (d) => d.Capitalizacion),
        acciones: acciones.map((d) => d.Ticker),
      })
    );
  };

  // Obtener datos para gráfico por sector
  const getDataForChart = () => {
    return d3.rollups(
      ipsaData,
      (v) => d3.sum(v, (d) => d.Capitalizacion),
      (d) => d.Sector
    ).map(([key, value]) => ({ name: key, value }));
  };

  return (
    <section className="datos-section">
      <div className="hero-datos">
        <h1>Recolección y Limpieza de Datos</h1>
        <p className="intro-text">
          En esta etapa del proyecto, nos enfocamos en garantizar que los datos
          utilizados para el análisis sean confiables, completos y
          representativos. Este proceso incluye tanto la recopilación de
          información financiera como su preparación para el análisis.
        </p>
      </div>

      {/* Explicación del IPSA y Yahoo Finance */}
      <div className="explanation">
        <h2>¿Qué es el IPSA?</h2>
        <p>
          El <strong>IPSA</strong> (Índice de Precios Selectivo de Acciones) es
          el principal indicador bursátil de Chile. Representa el desempeño de
          las acciones más importantes de la Bolsa de Santiago, lo que lo
          convierte en un termómetro del mercado financiero chileno.
        </p>
      </div>

      {/* Detalle de las etapas */}
      <div className="steps">
        <h2>¿Qué se hace en esta etapa?</h2>
        <ol>
          <li>
            <strong>Obtención de precios históricos:</strong>
            <ul>
              <li>
                Se recopilan los precios de las acciones principales del IPSA
                usando fuentes confiables, como APIs financieras (ejemplo:
                Yahoo Finance).
              </li>
              <li>
                Esto asegura que los datos sean precisos y representativos del
                comportamiento real del mercado.
              </li>
            </ul>
          </li>
          <li>
            <strong>Limpieza de datos:</strong>
            <ul>
              <li>
                <strong>Eliminación de inconsistencias:</strong> Si se detectan
                errores en los datos (como precios irreales), estos son
                corregidos o eliminados.
              </li>
              <li>
                <strong>Relleno de valores faltantes:</strong> Si hay días con
                datos incompletos, estos huecos se rellenan de manera lógica
                para evitar distorsiones en los análisis.
              </li>
              <li>
                <strong>Exclusión de datos anómalos:</strong> Los valores
                extremos o anómalos que puedan distorsionar los resultados son
                identificados y eliminados (por ejemplo, un precio que sube o
                baja drásticamente sin una causa justificada).
              </li>
            </ul>
          </li>
        </ol>
      </div>

      {loading ? (
        <div className="loading">Cargando datos...</div>
      ) : (
        <div className="chart-row">
          <TablaPorSector data={getActionsBySector()} />
          <GraficoPorSector
            data={getDataForChart()}
            onDrilldown={(sector) => console.log("Drilldown en", sector)}
          />
        </div>
      )}
    </section>
  );
};

export default Datos;
