from pathlib import Path
import math
import random
import sys

import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"
DATA_DIR = ROOT_DIR / "data"
GRAPH_CACHE_DIR = DATA_DIR / "osmnx_graphs"

sys.path.insert(0, str(SRC_DIR))

from approximate_index_builder import build_approximate_spatial_index
from establishments import load_establishments
from geo_distance import haversine_distance

CSV_PATH = DATA_DIR / "bares.csv"
NEIGHBORHOODS_PATH = DATA_DIR / "bairros" / "bh_neighborhood.json"
MAX_RADIUS_METERS = 2000
GRAPH_BUFFER_METERS = 1500
GRAPH_RADIUS_METERS = MAX_RADIUS_METERS + GRAPH_BUFFER_METERS
COURIER_SPEED_KMH = 20
COURIER_GENERATION_VERSION = 2


st.set_page_config(
    page_title="Busca Geoespacial — Belo Horizonte",
    page_icon="📍",
    layout="wide",
)


@st.cache_resource
def load_index(csv_path, neighborhoods_path):
    return build_approximate_spatial_index(
        csv_path,
        neighborhoods_path,
        precision=8,
    )


@st.cache_data
def load_search_records(csv_path):
    return load_establishments(csv_path)


@st.cache_resource(show_spinner=False)
def load_street_graph(latitude, longitude):
    """Carrega e reutiliza o grafo viário OSM da região do estabelecimento."""
    import osmnx as ox

    GRAPH_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_path = GRAPH_CACHE_DIR / (
        f"drive_{latitude:.5f}_{longitude:.5f}_{GRAPH_RADIUS_METERS}.graphml"
    )

    graph = None
    if cache_path.exists():
        try:
            graph = ox.load_graphml(filepath=cache_path)
        except Exception:
            # Se um arquivo de cache estiver incompleto/incompatível, recriá-lo.
            cache_path.unlink(missing_ok=True)

    if graph is None:
        graph = ox.graph_from_point(
            center_point=(float(latitude), float(longitude)),
            dist=GRAPH_RADIUS_METERS,
            dist_type="bbox",
            network_type="drive",
            simplify=True,
            retain_all=False,
        )
        if graph.number_of_nodes() == 0 or graph.number_of_edges() == 0:
            raise RuntimeError(
                "O OpenStreetMap não retornou ruas para essa região."
            )
        ox.save_graphml(graph, filepath=cache_path)

    if graph.number_of_nodes() == 0 or graph.number_of_edges() == 0:
        raise RuntimeError("O grafo viário carregado está vazio.")

    # O grafo projetado permite localizar arestas com distância em metros.
    return ox.project_graph(graph)


def generate_couriers(latitude, longitude, count, radius_meters, street_graph):
    """Gera pontos aleatórios e os ajusta à aresta viária mais próxima."""
    import osmnx as ox
    from pyproj import Transformer
    from shapely.geometry import LineString, Point
    from shapely.ops import nearest_points

    candidates = []
    for number in range(1, count + 1):
        distance = radius_meters * math.sqrt(random.random())
        angle = random.uniform(0, 2 * math.pi)

        delta_lat = (distance * math.cos(angle)) / 111195
        cos_lat = max(abs(math.cos(math.radians(latitude))), 0.01)
        delta_lon = (distance * math.sin(angle)) / (111195 * cos_lat)

        candidates.append(
            {
                "id": f"ENT-{number:03d}",
                "latitude": max(-90, min(90, latitude + delta_lat)),
                "longitude": max(-180, min(180, longitude + delta_lon)),
            }
        )

    to_projected = Transformer.from_crs(
        "EPSG:4326", street_graph.graph["crs"], always_xy=True
    )
    to_geographic = Transformer.from_crs(
        street_graph.graph["crs"], "EPSG:4326", always_xy=True
    )

    longitudes = [point["longitude"] for point in candidates]
    latitudes = [point["latitude"] for point in candidates]
    xs, ys = to_projected.transform(longitudes, latitudes)

    # Busca vetorizada: encontra a rua mais próxima para todos os pontos.
    nearest_edge_ids = ox.distance.nearest_edges(
        street_graph,
        X=list(xs),
        Y=list(ys),
    )

    couriers = []
    for candidate, x, y, edge_id in zip(candidates, xs, ys, nearest_edge_ids):
        u, v, key = (int(value) for value in edge_id)
        edge_data = street_graph.edges[u, v, key]
        geometry = edge_data.get("geometry")

        if geometry is None:
            geometry = LineString(
                [
                    (street_graph.nodes[u]["x"], street_graph.nodes[u]["y"]),
                    (street_graph.nodes[v]["x"], street_graph.nodes[v]["y"]),
                ]
            )

        # Projeta o ponto sobre a geometria da rua, não apenas sobre um nó.
        snapped_point = nearest_points(Point(float(x), float(y)), geometry)[1]
        snapped_lon, snapped_lat = to_geographic.transform(
            snapped_point.x, snapped_point.y
        )

        couriers.append(
            {
                "id": candidate["id"],
                "latitude": float(snapped_lat),
                "longitude": float(snapped_lon),
            }
        )

    return couriers


def main():
    # Invalida entregadores antigos, gerados antes do ajuste à malha viária.
    if st.session_state.get("courier_generation_version") != COURIER_GENERATION_VERSION:
        st.session_state.pop("couriers", None)
        st.session_state.pop("courier_center_id", None)
        st.session_state["courier_generation_version"] = COURIER_GENERATION_VERSION

    st.title("📍 Busca Geoespacial — Belo Horizonte")
    st.write(
        "Explore estabelecimentos por proximidade e visualize "
        "entregadores sintéticos em um mapa interativo."
    )

    st.warning(
        "Limitação dos dados: os estabelecimentos usam pontos "
        "representativos dos bairros, não coordenadas reais dos "
        "endereços. Distâncias e resultados são aproximados. "
        "Os entregadores são ajustados à rua mais próxima disponível "
        "no grafo viário do OpenStreetMap."
    )

    if not CSV_PATH.exists():
        st.error(f"Arquivo de dados não encontrado: {CSV_PATH}")
        st.stop()

    if not NEIGHBORHOODS_PATH.exists():
        st.error(
            "Arquivo de bairros não encontrado: "
            f"{NEIGHBORHOODS_PATH}"
        )
        st.stop()

    try:
        with st.spinner("Construindo o índice geoespacial..."):
            index, summary = load_index(
                str(CSV_PATH),
                str(NEIGHBORHOODS_PATH),
            )
            records = load_search_records(str(CSV_PATH))
    except Exception as error:
        st.error(f"Não foi possível carregar os dados: {error}")
        st.stop()

    indexed_records = list(index._records.values())
    indexed_by_id = {
        str(record["id"]): record for record in indexed_records
    }

    query = st.text_input(
        "Buscar estabelecimento por nome, rua ou bairro",
        placeholder="Ex.: restaurante, Avenida Brasil...",
    ).strip().casefold()

    filtered_records = [
        record
        for record in records
        if query
        in " ".join(
            [
                record.get("name", ""),
                record.get("address", ""),
                record.get("neighborhood", ""),
            ]
        ).casefold()
    ]

    selectable = [
        record
        for record in filtered_records
        if str(record["id"]) in indexed_by_id
    ]

    if not selectable:
        st.info(
            "Nenhum estabelecimento indexado corresponde à busca. "
            "Tente outro nome, endereço ou bairro."
        )
        st.metric("Estabelecimentos no índice", f"{len(index):,}")
        st.caption(
            f"Base: {summary['total_establishments']:,} registros; "
            f"{summary['unmatched']:,} sem correspondência de bairro."
        )
        return

    selectable_by_id = {
        str(record["id"]): record for record in selectable
    }

    def format_establishment(record_id):
        record = selectable_by_id[record_id]
        return (
            f"{record.get('name') or 'Sem nome'} — "
            f"{record.get('neighborhood') or 'Bairro não informado'} "
            f"(ID {record_id})"
        )

    selected_id = st.selectbox(
        "Selecione o estabelecimento de referência",
        options=list(selectable_by_id),
        format_func=format_establishment,
    )

    selected = indexed_by_id[selected_id]
    latitude = selected["latitude"]
    longitude = selected["longitude"]

    left, right = st.columns(2)

    with left:
        radius_meters = st.slider(
            "Raio da busca (metros)",
            min_value=100,
            max_value=MAX_RADIUS_METERS,
            value=1000,
            step=100,
        )

    with right:
        courier_count = st.number_input(
            "Quantidade de entregadores sintéticos",
            min_value=1,
            max_value=200,
            value=30,
            step=5,
        )

    results = index.search_radius(latitude, longitude, radius_meters)

    st.subheader("Resumo")
    col1, col2, col3 = st.columns(3)
    col1.metric("Estabelecimentos indexados", f"{len(index):,}")
    col2.metric("Encontrados no raio", f"{len(results):,}")
    col3.metric("Raio selecionado", f"{radius_meters} m")

    st.caption(
        f"Base original: {summary['total_establishments']:,} registros. "
        f"Indexados: {summary['indexed']:,}. "
        f"Sem correspondência de bairro: {summary['unmatched']:,}."
    )

    if st.button("Gerar / substituir entregadores", type="primary"):
        # Não deixa entregadores antigos na tela se a geração falhar.
        st.session_state.pop("couriers", None)
        st.session_state.pop("courier_center_id", None)
        try:
            with st.spinner(
                "Carregando a malha viária do OpenStreetMap e ajustando "
                "os entregadores às ruas. Na primeira execução pode demorar..."
            ):
                street_graph = load_street_graph(
                    round(float(latitude), 5),
                    round(float(longitude), 5),
                )
                new_couriers = generate_couriers(
                    latitude,
                    longitude,
                    int(courier_count),
                    radius_meters,
                    street_graph,
                )
            st.session_state["couriers"] = new_couriers
            st.session_state["courier_center_id"] = selected_id
            st.session_state["courier_generation_version"] = COURIER_GENERATION_VERSION
            st.success(
                f"{len(new_couriers)} entregadores posicionados na malha viária."
            )
        except Exception as error:
            st.error(
                "Não foi possível carregar ou usar a malha viária do "
                "OpenStreetMap. Verifique a conexão com a internet e tente "
                f"novamente. Detalhes técnicos: {error}"
            )

    couriers = st.session_state.get("couriers", [])
    couriers_match = st.session_state.get("courier_center_id") == selected_id

    if couriers and not couriers_match:
        st.info(
            "A referência foi alterada. Gere novamente os entregadores "
            "para posicioná-los ao redor do estabelecimento selecionado."
        )
        couriers = []

    map_view = folium.Map(
        location=[latitude, longitude],
        zoom_start=14,
        control_scale=True,
    )

    folium.Marker(
        [latitude, longitude],
        tooltip=selected.get("name", "Estabelecimento selecionado"),
        popup=(
            f"{selected.get('name', 'Sem nome')}<br>"
            f"{selected.get('address', '')}"
        ),
        icon=folium.Icon(color="pink", icon="cutlery", prefix="fa"),
    ).add_to(map_view)

    folium.Circle(
        location=[latitude, longitude],
        radius=radius_meters,
        color="blue",
        fill=True,
        fill_opacity=0.08,
        tooltip=f"Raio de {radius_meters} metros",
    ).add_to(map_view)

    for record in results:
        if str(record["id"]) == selected_id:
            continue

        folium.CircleMarker(
            location=[record["latitude"], record["longitude"]],
            radius=5,
            color="blue",
            fill=True,
            fill_opacity=0.7,
            tooltip=record.get("name", "Estabelecimento"),
            popup=(
                f"{record.get('name', 'Sem nome')}<br>"
                f"Bairro: {record.get('neighborhood', '')}<br>"
                f"Distância aproximada: "
                f"{record['distance_meters']:.0f} m"
            ),
        ).add_to(map_view)

    courier_rows = []
    available_count = 0
    unavailable_count = 0

    for courier in couriers:
        distance = haversine_distance(
            latitude,
            longitude,
            courier["latitude"],
            courier["longitude"],
        )
        available = distance <= radius_meters
        eta_minutes = distance / 1000 / COURIER_SPEED_KMH * 60
        status = "Disponível" if available else "Indisponível"
        marker_color = "green" if available else "gray"

        if available:
            available_count += 1
        else:
            unavailable_count += 1

        courier_rows.append(
            {
                "ID": courier["id"],
                "Distância aproximada (m)": round(distance, 1),
                "ETA estimado (min)": round(eta_minutes, 1),
                "Status": status,
                "Latitude": round(courier["latitude"], 6),
                "Longitude": round(courier["longitude"], 6),
            }
        )

        folium.Marker(
            [courier["latitude"], courier["longitude"]],
            tooltip=f"{courier['id']} — {status}",
            popup=(
                f"Entregador: {courier['id']}<br>"
                f"Distância aproximada: {distance:.0f} m<br>"
                f"Raio selecionado: {radius_meters} m<br>"
                f"Status: {status}<br>"
                f"ETA estimado: {eta_minutes:.1f} min"
            ),
            icon=folium.Icon(
                color=marker_color,
                icon="bicycle",
                prefix="fa",
            ),
        ).add_to(map_view)

    st.subheader("Mapa interativo")
    st_folium(map_view, width=None, height=520, key="geospatial_map")

    st.subheader("Estabelecimentos encontrados")
    if results:
        establishments_table = pd.DataFrame(
            [
                {
                    "ID": str(record["id"]),
                    "Nome": record.get("name", ""),
                    "Bairro": record.get("neighborhood", ""),
                    "Endereço": record.get("address", ""),
                    "Distância aproximada (m)": round(
                        record["distance_meters"], 1
                    ),
                }
                for record in results
            ]
        )
        st.dataframe(
            establishments_table,
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("Nenhum resultado dentro do raio selecionado.")

    st.subheader("Entregadores sintéticos")
    if courier_rows:
        metric1, metric2, metric3 = st.columns(3)
        metric1.metric("Entregadores gerados", len(courier_rows))
        metric2.metric("Disponíveis", available_count)
        metric3.metric("Indisponíveis", unavailable_count)

        courier_table = pd.DataFrame(courier_rows)
        st.dataframe(
            courier_table,
            use_container_width=True,
            hide_index=True,
        )
        st.caption(
            f"ETA calculado com velocidade constante de "
            f"{COURIER_SPEED_KMH} km/h e distância em linha reta. "
            "Não representa tempo real de percurso pelas ruas."
        )
    else:
        st.info(
            "Clique em “Gerar / substituir entregadores” para "
            "simular entregadores próximos ao estabelecimento. "
            "Na primeira geração, a malha viária será baixada do OpenStreetMap."
        )


if __name__ == "__main__":
    main()
