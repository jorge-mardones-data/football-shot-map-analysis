import pandas as pd
import json
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from matplotlib.patches import Rectangle, Arc
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.gridspec import GridSpec, GridSpecFromSubplotSpec
from matplotlib.patches import Rectangle
from matplotlib.patches import RegularPolygon
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable

#CARGAR DATOS---------------------------------------------------------------------

def load_events(file_path):
    with open(file_path,encoding="utf-8") as f:
        events = json.load(f)
    return events

project_root = Path(__file__).resolve().parent.parent
file_path = project_root / "data" / "raw" / "events" / "69299.json"
events = load_events(file_path)

#Pasar a dataframe
df = pd.json_normalize(events)

#DEFINIR EQUIPO 1 Y EQUIPO 2
#EQUIPO DE INTERES (BARCELONA) SERÁ EQUIPO 1
team_1="Barcelona"
team_home=df["team.name"][0]
team_away=df["team.name"][1]

if team_1 not in (team_home,team_away):
    raise ValueError(
        "{} no participa en el partido.".format(team_1)
    )

if team_1 == team_home:
    team_2= team_away
else:
    team_2= team_home

#CONSTRUIR DF DE SHOTS DEL EQUIPO DE INTERES ----------------------------------------------
shots=df[df["type.name"]=="Shot"].copy()

#conservar solo los tiros de equipo de interes
shots_team=shots[shots["team.name"]==team_1]

#construir el df
shots_team=shots_team[["player.name", "minute", "second", "location","shot.statsbomb_xg","shot.outcome.name","shot.type.name","shot.body_part.name"]]
#Crear coordenadas x,y
shots_team["x"] = shots_team["location"].apply(lambda x: x[0])
shots_team["y"] = shots_team["location"].apply(lambda x: x[1])

#CREAR LAS ZONAS PARTICIONANDO EL CAMPO --------------------------------------------------------------
#zonas 0-18
#zonificacion, creamos la funcion zone
def zone(x,y):
    if 0<=x<20:
        if 0<=y<26.67:
            return 1
        elif 26.67<=y<53.33:
            return 2
        elif 53.33<=y<80:
            return 3
    elif 20<=x<40:
        if 0<=y<26.67:
            return 4
        elif 26.67<=y<53.33:
            return 5
        elif 53.33<=y<80:
            return 6
    elif 40<=x<60:
        if 0<=y<26.67:
            return 7
        elif 26.67<=y<53.33:
            return 8
        elif 53.33<=y<80:
            return 9
    elif 60<=x<80:
        if 0<=y<26.67:
            return 10
        elif 26.67<=y<53.33:
            return 11
        elif 53.33<=y<80:
            return 12
    elif 80<=x<100:
        if 0<=y<26.67:
            return 13
        elif 26.67<=y<53.33:
            return 14
        elif 53.33<=y<80:
            return 15
    elif 100<=x<120:
        if 0<=y<26.67:
            return 16
        elif 26.67<=y<53.33:
            return 17
        elif 53.33<=y<80:
            return 18

shots_team['zone'] = shots_team.apply(lambda row: zone(row['x'], row['y']), axis=1)
zone_counts = (shots_team["zone"].value_counts().sort_index())

#CREAR EL MAPA ZONAL ------------------------------------------------------------------------

#Contar cuántos tiros hay en cada zona (del 1 al 18)
counts = shots_team['zone'].value_counts().reindex(range(1,19), fill_value=0).sort_index().values

#Convertir el vector de 18 elementos en una matriz de 3 filas y 6 columnas (3x6)
grid_counts = counts.reshape((3, 6),order="F")

#Graficar la matriz como un mapa de calor básico
plt.figure(figsize=(10, 6))
plt.imshow(grid_counts, cmap='YlOrRd', origin='upper', extent=[0, 120, 0, 80])

#Agregar los números dentro de cada celda para ver las cantidades exactas
x_centers = np.linspace(10, 110, 6)
y_centers = np.linspace(80 - 13.33, 13.33, 3) # De arriba hacia abajo si origin='upper'

for i in range(3):
    for j in range(6):
        # Dibujar el número de tiros en el centro de la celda
        plt.text(x_centers[j], y_centers[i], str(grid_counts[i, j]),
                 ha='center', va='center', color='black', fontsize=12, fontweight='bold')

#Configurar límites del campo de juego y etiquetas
plt.xlim(0, 120)
plt.ylim(0, 80)
plt.xlabel('Largo del campo')
plt.ylabel('Ancho del campo')
plt.title('Mapa de Calor de Tiros por Zona - {}'.format(team_1))
plt.colorbar(label='Cantidad de tiros')

#Mostrar el gráfico
#plt.show()

#CONSTRUCCIÓN DE LA VISUALIZACIÓN DEFINITIVA-------------------------------------------------------------

#Transformar coordenadas
shots_team["plot_x"]=shots_team["location"].apply(lambda p: p[1])
shots_team["plot_y"]=shots_team["location"].apply(lambda p: 120 - p[0])

#CONSTRUCCION DEL CAMPO


#CONSTRUCCION DE FUNCION QUE CONVIERTE LOS TIROS
#elegir prioridad
def determinar_forma(row):
    if row["shot.type.name"] == "Free Kick":
        return "Free Kick"
    elif row["shot.body_part.name"] == "Head":
        return "Head"
    else:
        return "Foot"

shots_team["shot_shape"]=shots_team.apply(determinar_forma,axis=1)

#Clasificar el resultado
def determinar_resultado(outcome):
    if outcome == "Goal":
        return "Goal"
    elif outcome == "Saved":
        return "Saved"
    elif outcome == "Blocked":
        return "Blocked"
    else:
        return "Off T/Other"

shots_team["visual_outcome"] = (shots_team["shot.outcome.name"].apply(determinar_resultado))

#ASIGNAR SIMBOLOS
marker_map = {"Head": "o","Foot": "h","Free Kick": "s"}
shots_team["marker"] = (shots_team["shot_shape"].map(marker_map))

#CREAR ESCALA DE COLOR
xg_cmap = LinearSegmentedColormap.from_list("xg_scale",["lightgreen", "yellow", "orange", "red", "darkred"])
norm = plt.Normalize(0,1)
xg_cmap(norm(shots_team["shot.statsbomb_xg"]))

#FUNCION DE REPRESENTACION DE UN TIRO
xg_cmap = LinearSegmentedColormap.from_list("xg_scale",["lightgreen", "yellow", "orange", "red", "darkred"])
xg_norm = plt.Normalize(0, 1)

#FORMA
def obtener_marker(shot_shape):
    marker_map = {"Head": "o","Foot": "h","Free Kick": "s"}
    return marker_map[shot_shape]

#Estilo del tiro
def obtener_estilo_tiro(row):
    resultado = row["visual_outcome"]

    #Color determinado por xG
    color = xg_cmap(xg_norm(row["shot.statsbomb_xg"]))

    #Valores por defecto
    alpha = 1.0
    edgecolor = "none"
    linewidth = 0
    
    # BLOCKED ------------------------
    if resultado == "Blocked":
        color = "lightgray"
        alpha = 0.55
        edgecolor = "gray"
        linewidth = 0.8
    
    # OFF T / OTHER ------------------
    elif resultado == "Off T/Other":
        alpha = 0.45
        edgecolor = "none"
        linewidth = 0
    
    # SAVED --------------------------
    elif resultado == "Saved":
        edgecolor = "black"
        linewidth = 2.2
    
    # GOAL ---------------------------
    elif resultado == "Goal":
        edgecolor = "black"
        linewidth = 2.2

    return color, alpha, edgecolor, linewidth

#FUNCION PARA DIBUJAR UN TIRO 
def dibujar_tiro(ax, row):
    marker = obtener_marker(row["shot_shape"])
    
    color = xg_cmap(xg_norm(row["shot.statsbomb_xg"]))
    resultado = row["visual_outcome"]
    

    #GOAL------------------------------
    if resultado == "Goal":
        #Capa exterior negra
        ax.scatter(
            row["plot_x"],
            row["plot_y"],
            marker=marker,
            s=170,
            facecolor="black",
            edgecolor="black",
            linewidth=0.3
        )
        # Capa interior xG
        ax.scatter(
            row["plot_x"],
            row["plot_y"],
            marker=marker,
            s=103,
            facecolor=color,
            edgecolor="black",
            linewidth=0.3
        )
    
    #SAVED -----------------------------
    elif resultado == "Saved":
        #Capa exterior gris clara
        ax.scatter(
            row["plot_x"],
            row["plot_y"],
            marker=marker,
            s=175,
            facecolor="lightgray",
            edgecolor="black",
            linewidth=0.3
        )
        #Capa interior xG
        ax.scatter(
            row["plot_x"],
            row["plot_y"],
            marker=marker,
            s=103,
            facecolor=color,
            edgecolor="black",
            linewidth=0.3
        )
    
    #BLOCKED ---------------------------
    elif resultado == "Blocked":
        ax.scatter(
            row["plot_x"],
            row["plot_y"],
            marker=marker,
            s=103,
            facecolor="lightgray",
            edgecolor="gray",
            linewidth=0.5,
            alpha=0.6
        )
    
    # OFF T / OTHER --------------------
    else:
        ax.scatter(
            row["plot_x"],
            row["plot_y"],
            marker=marker,
            s=103,
            facecolor=color,
            edgecolor="grey",
            linewidth=0.5,
            alpha=0.6
        )


#CAMPO 
def dibujar_campo(ax):
    ax.set_xlim(0, 80)
    ax.set_ylim(60, 0)
    ax.set_aspect("equal")

    campo = Rectangle((0, 0),80,60,fill=False,linewidth=1.5)
    ax.add_patch(campo)

    area_grande = Rectangle((18, 0),44,18,fill=False,linewidth=0.8)
    ax.add_patch(area_grande)

    area_chica = Rectangle((30, 0),20,6,fill=False,linewidth=0.9)
    ax.add_patch(area_chica)

    ax.scatter(40,12.6,s=10)

    arco = Arc((40, 12.6),width=18.3,height=18.3,theta1=36,theta2=144,linewidth=0.9)
    ax.add_patch(arco)

    portería = Rectangle((36, -3),8,3,fill=False,linewidth=1.5)
    ax.add_patch(portería)

    ax.set_xticks([])
    ax.set_yticks([])

    for spine in ax.spines.values():
        spine.set_visible(False)


#CONSTRUIR VISUALIZACION --------------------------------------------------------------------

fig = plt.figure(figsize=(13, 9),facecolor="white")

gs = GridSpec(nrows=3,ncols=1,figure=fig,height_ratios=[1.45, 7.8, 0.45],hspace=0.05)

ax_header = fig.add_subplot(gs[0])
ax_body = fig.add_subplot(gs[1])
ax_footer = fig.add_subplot(gs[2])

header_bg = Rectangle((0, 0),1,1,transform=ax_header.transAxes,facecolor="#EAEAEA",edgecolor="none",zorder=0)
ax_header.add_patch(header_bg)
ax_header.axis("off")

body_gs = GridSpecFromSubplotSpec(nrows=1,ncols=2,subplot_spec=gs[1],width_ratios=[4.7, 1.3],wspace=0.03)
ax_field = fig.add_subplot(body_gs[0])
ax_panel = fig.add_subplot(body_gs[1])
ax_body.axis("off")
ax_panel.axis("off")

ax_footer.axis("off")
#HEADER ----------------------------------------------------------


ax_header.text(0.02, 0.72, "{} — Shot Map".format(team_1),
    fontsize=18,fontweight="bold",
    ha="left",va="center")

ax_header.text(0.02, 0.42, "vs {}".format(team_2),
    fontsize=14,
    ha="left",va="center")

ax_header.text(0.02, 0.08, "From which areas did {} finish their attacks with shots, and what were the outcomes?".format(team_1),
    fontsize=10.5,
    ha="left",va="bottom")

#esquina superior derecha

ax_header.text(0.98, 0.78, "Data: Statsbomb Open Data | Unit: {} Shots".format(team_1),
    fontsize=9,
    ha="right",va="center")

ax_header.text(0.98, 0.58, "Scope: Single-match descriptive analysis",
    fontsize=9,
    ha="right",va="center")

ax_header.text(0.98, 0.38, "@jorge-mardones-data",
    fontsize=9,
    ha="right",va="center")


#CAMPO -------------------------------------------------------------
dibujar_campo(ax_field)

for _, row in shots_team.iterrows():
    dibujar_tiro(ax_field, row)

#LEYENDA -----------------------------------------------------------

#funcion que dibuja la leyenda
def dibujar_marcador_leyenda(ax,x,y,outcome,xg_color):
    #GOAL
    if outcome == "Goal":
        ax.scatter(x, y,marker="h",
            s=85,
            facecolor="black",
            edgecolor="black",
            linewidth=0.2, alpha=0.7)
        
        ax.scatter(x, y,marker="h",
            s=45,
            facecolor="white",
            edgecolor="black",
            linewidth=0.2)
    #SAVED
    elif outcome == "Saved":
        ax.scatter(x, y,marker="h",
            s=85,
            facecolor="lightgray",
            edgecolor="black",
            linewidth=0.2)
        
        ax.scatter(x, y,marker="h",
            s=45,
            facecolor="white",
            edgecolor="black",
            linewidth=0.2)
    #BLOCKED
    elif outcome == "Blocked":
        ax.scatter(x, y,marker="h",
            s=45,
            facecolor="lightgray",
            edgecolor="gray",
            linewidth=0.5,alpha=0.7)
    #OFF T / OTHER
    elif outcome == "Off T / Other":
        ax.scatter(x, y,marker="h",
            s=45,
            facecolor="white",
            edgecolor="gray",
            linewidth=0.5,alpha=0.7)

#funcion que crea la leyenda
def crear_leyenda_shotmap(ax,xg_cmap,xg_norm):

    legend_ax = ax.inset_axes([0.035, 0.025, 0.93, 0.20])
    legend_ax.set_xlim(0, 1)
    legend_ax.set_ylim(0, 1)
    legend_ax.axis("off")
    legend_ax.patch.set_facecolor("white")
    legend_ax.patch.set_alpha(0.72)
    text_color = "dimgray"
    
    #TYPE ---------------
    type_items = [(0.03, 0.65, "o", "Head"),
        (0.03, 0.43, "h", "Foot / Other"),
        (0.03, 0.21, "s", "Freekick / Penalty")]
    
    for x, y, marker, label in type_items:

        legend_ax.scatter(x, y,marker=marker,
            s=60,
            facecolor="white",
            edgecolor="gray",
            linewidth=0.8,alpha=0.85)
        
        legend_ax.text(x + 0.035,y,
            label,fontsize=7,
            color=text_color,alpha=0.7,
            ha="left",va="center")
    
    #OUTCOME --------------
    example_xg = xg_cmap(xg_norm(0.50))
    
    outcomes = [
        (0.27, 0.74, "Goal"),
        (0.27, 0.52, "Saved"),
        (0.27, 0.3, "Blocked"),
        (0.27, 0.08, "Off T / Other")]
    
    for x, y, outcome in outcomes:
        dibujar_marcador_leyenda(legend_ax,x,y,outcome,example_xg)
        
        legend_ax.text(x + 0.035,y,
            outcome,
            fontsize=7,
            color=text_color,alpha=0.7,
            ha="left",va="center")
    
    #xG -----------------------
    x_values = np.linspace(0, 1, 120)
    
    gradient = np.array([
        xg_cmap(xg_norm(x))
        for x in x_values
    ]).reshape(1, -1, 4)
    
    legend_ax.imshow(gradient, extent=[0.62, 0.87, 0.18, 0.30], aspect="auto")
    
    legend_ax.text(0.62, 0.05,"lower", 
        fontsize=7,color=text_color,
        alpha=0.8,ha="left")
    
    legend_ax.text(0.87, 0.05,"higher",
        fontsize=7,color=text_color,
        alpha=0.8,ha="right")

crear_leyenda_shotmap(ax_field,xg_cmap,xg_norm)

#PANEL DERECHO ------------------------------------------------------

def dibujar_metricas(ax, shots):
    total_shots = len(shots)
    total_goals = (shots["visual_outcome"] == "Goal").sum()
    total_xg = shots["shot.statsbomb_xg"].sum()

    metrics = [(f"{total_shots}", "SHOTS"),(f"{total_goals}", "GOALS"),(f"{total_xg:.2f}", "TOTAL xG")]
    y_positions = [0.88, 0.69, 0.50]

    for (value, label), y in zip(metrics, y_positions):
        ax.text(0.5, y,value,
            fontsize=18,
            fontweight="bold",
            ha="center",va="center")

        ax.text(0.5, y - 0.055,
            label,fontsize=8.5,
            ha="center",va="center")

dibujar_metricas(ax_panel,shots_team)

#FINDINGS --------------------------------------------------------

def dibujar_findings(ax, shots):
    total = len(shots)
    central_zones = [14, 17]
    central_shots = shots[shots["zone"].isin(central_zones)]

    zone_17 = shots[shots["zone"] == 17]

    central_pct = len(central_shots) / total * 100
    zone_17_pct = len(zone_17) / total * 100

    ax.text(0.5, 0.31,"KEY FINDINGS",
        fontsize=9,
        fontweight="bold",
        ha="center",
        va="center")

    ax.text(0.5, 0.22, f"{central_pct:.0f}%",
        fontsize=18,
        fontweight="bold",
        ha="center",
        va="center")
    ax.text(0.5, 0.175, "of shots came from the",
        fontsize=8,
        ha="center",
        va="center")
    ax.text(0.5, 0.14, "central sector",
        fontsize=8,
        ha="center",
        va="center")

    ax.text(0.5, 0.075, f"{zone_17_pct:.0f}%",
        fontsize=18,
        fontweight="bold",
        ha="center",
        va="center")
    ax.text(0.5, 0.035, "of shots came from the",
        fontsize=8,
        ha="center",
        va="center")
    ax.text(0.5, 0.000, "main finishing zone (17)",
        fontsize=8,
        ha="center",
        va="center")

dibujar_findings(ax_panel,shots_team)

#FOOTER -----------------------------------------------------------

ax_footer.text(0.5,0.5, "Results describe this match and should not be interpreted as general team tendencies.",
    fontsize=8,
    style="italic",
    color="dimgray",
    ha="center",va="bottom")

plt.show()
