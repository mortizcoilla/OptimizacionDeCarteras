import React from "react";
import "./App.css";

// Importaciones de los componentes
import Datos from "./components/Datos/Datos";
import Exploracion from "./components/Exploracion/Exploracion";
import Modelado from "./components/Modelado/Modelado";
import Optimizacion from "./components/Optimizacion/Optimizacion";
import Desempeno from "./components/Desempeño/Desempeño";
import Monitoreo from "./components/Monitoreo/Monitoreo";
import Documentacion from "./components/Documentacion/Documentacion";

const App = () => {
  // Función de scroll suave
  const handleScroll = (id) => {
    const section = document.getElementById(id);
    if (section) {
      section.scrollIntoView({ behavior: "smooth" });
    }
  };

  return (
    <div>
      {/* Navbar */}
      <header className="navbar">
        <nav>
          <ul className="navbar-links">
            <li onClick={() => handleScroll("inicio")}>Inicio</li>
            <li onClick={() => handleScroll("datos")}>Datos</li>
            <li onClick={() => handleScroll("exploracion")}>Exploración</li>
            <li onClick={() => handleScroll("modelado")}>Modelado</li>
            <li onClick={() => handleScroll("optimizacion")}>Optimización</li>
            <li onClick={() => handleScroll("desempeno")}>Desempeño</li>
            <li onClick={() => handleScroll("monitoreo")}>Monitoreo</li>
            <li onClick={() => handleScroll("documentacion")}>Documentación</li>
          </ul>
        </nav>
      </header>

      {/* Hero Section */}
      <section id="inicio" className="hero">
        <div className="hero-content">
          <h1>Optimización de Carteras de Inversión</h1>
          <p>
            Análisis avanzado para maximizar la rentabilidad y minimizar riesgos.
          </p>
        </div>
      </section>

      {/* Secciones */}

      <section id="datos">
        <Datos />
      </section>

      <section id="exploracion">
        <Exploracion />
      </section>

      <section id="modelado">
        <Modelado />
      </section>

      <section id="optimizacion">
        <Optimizacion />
      </section>

      <section id="desempeno">
        <Desempeno />
      </section>

      <section id="monitoreo">
        <Monitoreo />
      </section>

      <section id="documentacion">
        <Documentacion />
      </section>

      {/* Footer */}
      <footer className="footer">
        <p>&copy; 2024 Miguel Ortiz C.</p>
      </footer>
    </div>
  );
};

export default App;
