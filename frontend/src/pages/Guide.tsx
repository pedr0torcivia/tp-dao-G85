import { Fragment, type ReactNode } from "react";
import { Link } from "react-router-dom";
import { ArrowRight } from "lucide-react";
import { Heading, PatternNote } from "../components/ui";

function Flow({ nodes }: { nodes: (string | [string, "final" | "bad"])[] }) {
  return (
    <div className="flow">
      {nodes.map((n, i) => {
        const [label, kind] = Array.isArray(n) ? n : [n, ""];
        return (
          <Fragment key={i}>
            {i > 0 && <ArrowRight size={14} className="arrow" />}
            <span className={`node ${kind}`}>{label}</span>
          </Fragment>
        );
      })}
    </div>
  );
}

function Card({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="card card-pad">
      <h2 className="card-title">{title}</h2>
      <div className="grid gap-3 text-sm leading-relaxed">{children}</div>
    </section>
  );
}

const estados: [string, string, string[]][] = [
  ["EnPreparacion", "Se arma el paquete", ["agregar", "quitar", "empaquetar", "cancelar"]],
  ["Empaquetado", "Paquete cerrado", ["reabrir", "despachar", "cancelar"]],
  ["EnTransito", "Viajando", ["recibir"]],
  ["Recibido", "Final, sin novedades", []],
  ["RecibidoConIncidencias", "Final, con daños o faltantes", []],
  ["Cancelado", "Final, anulado", []],
];
const ops = ["agregar", "quitar", "empaquetar", "reabrir", "despachar", "recibir", "cancelar"];

const reglas: [string, string][] = [
  ["No prestar ejemplares no disponibles", "Asignar exige estado Disponible y condición Apto."],
  ["No prestar a socios inhabilitados", "Se controla al crear, asignar, despachar y entregar."],
  ["Controlar vencimientos", "Plazo máximo de 60 días; un socio con préstamos vencidos no retira material nuevo; multa por día de atraso."],
  ["Trazabilidad del remito", "Cada transición deja un evento con fecha, responsable y observación."],
  ["Evitar duplicados", "Socio (número y documento), libro (ISBN o edición), ejemplar (código) y remito (número) son únicos."],
  ["Ejemplar de la sede de origen", "La copia asignada debe pertenecer y estar en la sede de origen de la solicitud."],
  ["Sedes dadas de baja", "No se crean solicitudes, reservas ni remitos, ni se despacha, desde o hacia una sede de baja."],
];

export function Guide() {
  return (
    <>
      <Heading
        kicker="Guía"
        title="Cómo funciona EntreLibros"
        description="El recorrido de un libro desde que un socio lo pide hasta que vuelve a su biblioteca, y los dos patrones de diseño que lo resuelven."
      />

      <div className="guide-grid">
        <Card title="Préstamo local">
          <p className="muted">El libro está en la misma sede donde el socio lo retira.</p>
          <Flow nodes={["Solicitud", "Asignar copia", "Lista en mostrador", "Entregar", "Préstamo", "Devolver", "Revisión", ["Disponible", "final"]]} />
        </Card>
        <Card title="Préstamo interbibliotecario">
          <p className="muted">El libro está en otra sede y viaja en un remito.</p>
          <Flow nodes={["Solicitud", "Asignar copia", "Remito", "Despachar", "Recibir", "Entregar", "Devolver", "Remito de retorno", ["Disponible", "final"]]} />
        </Card>
        <Card title="Reserva">
          <p className="muted">Cuando no hay copias libres en la sede de retiro.</p>
          <Flow nodes={["Reserva en espera", "Apartar copia", "Lista para retirar", ["Entregada", "final"]]} />
          <Flow nodes={["Lista para retirar", ["Vence el plazo → expirada", "bad"]]} />
        </Card>
        <Card title="Dónde empezar">
          <p>
            La <Link className="font-semibold text-[var(--primary)] underline" to="/inicio">Mesa de trabajo</Link>{" "}
            muestra lo que tu sede tiene que resolver, cada fila con el botón del paso siguiente.
            Cambiá de sede desde la barra lateral para ver la jornada de otra biblioteca.
          </p>
          <p>
            Para un pedido nuevo usá <b>Nueva solicitud</b>: elegís socio, libro y sede de retiro, y la
            pantalla te muestra dónde hay copias y si el préstamo será local o interbibliotecario.
          </p>
        </Card>
      </div>

      <h2 className="section-title">Patrón State · ciclo de vida del remito</h2>
      <div className="guide-grid">
        <Card title="Qué resuelve">
          <p>
            Un remito se comporta distinto según su estado: en preparación acepta ejemplares; empaquetado
            se puede despachar o reabrir; en tránsito sólo se puede recibir. En lugar de un{" "}
            <code className="code">if estado == …</code> en cada servicio, cada estado es una clase.
          </p>
          <ul className="grid gap-1.5">
            <li>
              <b>Contexto:</b> <code className="code">Remito</code> — expone{" "}
              <code className="code">remito.comportamiento</code> y{" "}
              <code className="code">transicionar()</code>, que registra el evento de trazabilidad.
            </li>
            <li>
              <b>Estado abstracto:</b> <code className="code">EstadoRemitoBase</code> — declara las 7
              operaciones y por defecto las rechaza.
            </li>
            <li>
              <b>Estados concretos:</b> redefinen sólo lo que admiten y aplican sus efectos (p. ej.{" "}
              <code className="code">Empaquetado.despachar()</code> pone los ejemplares en tránsito).
            </li>
          </ul>
          <p className="muted">
            Código: <code className="code">backend/apps/logistica/states.py</code>. La API devuelve{" "}
            <code className="code">estado_clase</code> y <code className="code">acciones</code>: la interfaz
            muestra sólo los botones que el estado admite.
          </p>
        </Card>
        <section className="card card-pad">
          <h2 className="card-title">Operaciones por estado</h2>
          <div className="table-wrap !shadow-none">
            <table>
              <thead>
                <tr>
                  <th>Clase</th>
                  {ops.map((o) => (
                    <th key={o} className="!px-2 text-center">{o}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {estados.map(([clase, desc, admite]) => (
                  <tr key={clase}>
                    <td>
                      <div className="cell-main mono">{clase}</div>
                      <div className="cell-sub">{desc}</div>
                    </td>
                    {ops.map((o) => (
                      <td key={o} className="!px-2 text-center">
                        {admite.includes(o) ? (
                          <span className="font-bold text-[var(--ok)]">✓</span>
                        ) : (
                          <span className="text-[var(--muted-foreground)]">·</span>
                        )}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      </div>

      <h2 className="section-title">Patrón Strategy · tramitación de la solicitud</h2>
      <div className="guide-grid">
        <Card title="Qué resuelve">
          <p>
            Preparar la entrega no es lo mismo si el libro está en la sede (se deja en mostrador) que si
            está en otra (hay que mandarlo en un remito). El servicio no pregunta por el tipo: le pide la
            estrategia a una fábrica y la usa.
          </p>
          <ul className="grid gap-1.5">
            <li>
              <b>Estrategia:</b> <code className="code">TramitacionPrestamo</code> —{" "}
              <code className="code">validar_creacion()</code> y <code className="code">preparar_entrega()</code>.
            </li>
            <li>
              <code className="code">TramitacionLocal</code>: exige misma sede; preparar deja la copia lista en mostrador.
            </li>
            <li>
              <code className="code">TramitacionInterbibliotecaria</code>: exige sedes distintas; preparar
              incorpora la copia a un remito hacia la sede de retiro (lo crea si hace falta). Así se conectan
              ambos patrones.
            </li>
            <li>
              <b>Fábrica:</b> <code className="code">obtener_estrategia(tipo)</code>.
            </li>
          </ul>
          <p className="muted">
            Código: <code className="code">backend/apps/circulacion/strategies/</code>. Agregar un circuito
            nuevo (por ejemplo, envío a domicilio) es sumar una clase, sin tocar los servicios.
          </p>
        </Card>
        <div className="grid gap-4">
          <PatternNote pattern="Strategy">
            En la ficha de cada solicitud vas a ver qué estrategia la tramita y qué hace al preparar la
            entrega. El botón es el mismo para los dos tipos; el resultado cambia.
          </PatternNote>
          <PatternNote pattern="State">
            En la ficha de cada remito vas a ver la clase de estado activa y qué operaciones admite (en
            verde) o rechaza (tachadas).
          </PatternNote>
        </div>
      </div>

      <h2 className="section-title">Reglas de negocio</h2>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Validación</th>
              <th>Cómo se aplica</th>
            </tr>
          </thead>
          <tbody>
            {reglas.map(([r, c]) => (
              <tr key={r}>
                <td className="cell-main">{r}</td>
                <td>{c}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
