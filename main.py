import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt, mpld3
from matplotlib.figure import Figure
from mpld3 import fig_to_html
import openai
import numpy as np
import random
import requests
import pickle
from streamlit.report_thread import get_report_ctx
from matplotlib.colors import to_hex
import os
from os import listdir
from dotenv import load_dotenv

load_dotenv()
token = os.environ.get("api-token")
openai.api_key = token

markersdict = {'.': 'point', ',': 'pixel', 'o': 'circle', 'v': 'triangle_down', '^': 'triangle_up', '<': 'triangle_left', '>': 'triangle_right', '1': 'tri_down', '2': 'tri_up', '3': 'tri_left', '4': 'tri_right', '8': 'octagon', 's': 'square', 'p': 'pentagon', '*': 'star', 'h': 'hexagon1', 'H': 'hexagon2', '+': 'plus', 'x': 'x', 'D': 'diamond', 'd': 'thin_diamond', '|': 'vline', '_': 'hline', 'P': 'plus_filled', 'X': 'x_filled', 0: 'tickleft', 1: 'tickright', 2: 'tickup', 3: 'tickdown', 4: 'caretleft', 5: 'caretright', 6: 'caretup', 7: 'caretdown', 8: 'caretleftbase', 9: 'caretrightbase', 10: 'caretupbase', 11: 'caretdownbase', 'None': 'nothing', None: 'nothing', ' ': 'nothing', '': 'nothing'}

### Customize UI
st.set_page_config(layout="wide", page_title="NLP2Chart", page_icon=":)")
#st.set_page_config(layout="wide")

st.markdown(""" <style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style> """, unsafe_allow_html=True)

st.markdown(f""" <style>
    .reportview-container .main .block-container{{
        padding-top: {0}rem;
        padding-right: {5}rem;
        padding-left: {3}rem;
        padding-bottom: {0}rem;
    }} </style> """, unsafe_allow_html=True)


### Session ID vergeben

#st.session_state.style = "ggplot"
plt.style.use('ggplot')
def get_session_id():
    session_id = get_report_ctx().session_id
    session_id = session_id.replace('-','_')
    session_id = '_id_' + session_id
    return session_id
st.session_state.id = str(get_session_id())

### Figure intialisieren

def init_widgets():
    if 'xaxis' in st.session_state:
        del st.session_state.xaxis
    if 'yaxis' in st.session_state:
        del st.session_state.yaxis
    if 'title' in st.session_state:
        del st.session_state.title
    if 'xlim_start' in st.session_state:
        del st.session_state.xlim_start
    if 'xlim_end' in st.session_state:
        del st.session_state.xlim_end
    if 'ylim_start' in st.session_state:
        del st.session_state.ylim_start
    if 'ylim_end' in st.session_state:
        del st.session_state.ylim_end
    return True

#fig = plt.gcf()
#contained_artists = fig.get_children()
#if len(contained_artists) <= 1:
fig = plt.figure()
ax = fig.add_subplot()
#ax.set_title("Figure Title")
with open('fig'+ st.session_state.id +'.pickle', 'wb') as f: # should be 'wb' rather than 'w'
    pickle.dump(fig, f)

### Layout Sidebar ###

# Style Selection
#st.sidebar.markdown('### Styles ###')
#option = st.sidebar.selectbox(
    #'Select a Base-Style', ('ggplot', 'default', 'dark_background', 'fivethirtyeight', 'grayscale', 'seaborn-dark', 'Solarize_Light2'))
#st.session_state.style = option
#st.sidebar.write('You selected:', option)

agree = st.sidebar.checkbox('Grid')
if agree:
    st.session_state.grid = 'plt.grid(True)'
else:
    st.session_state.grid = 'plt.grid(False)'

st.sidebar.markdown('### Datasets ###')
# Data Selection
datafiles = ['No Dataset'] + [file for file in listdir(".") if file.endswith('.csv')]
option = st.sidebar.selectbox(
    'Which dataset do you want to use?',
     datafiles, key = 'dataset', on_change=init_widgets)

# File Upload
uploaded_file = st.sidebar.file_uploader("Or upload a file", type= ['csv'], key = 'fileupload', on_change=init_widgets)
if uploaded_file != None:
    try:
        dataframe = pd.read_csv(uploaded_file)
        dataframe.to_csv(uploaded_file.name)
        option = uploaded_file.name
    except:
        st.sidebar.write("Could not import")

if option in datafiles:
    ind = datafiles.index(option)
    if option != 'No Dataset':
        st.session_state.comand_load = "pd.read_csv(" + datafiles[ind]+"\')"
        st.session_state.prompt_load = "Load "+ datafiles[ind] +" into a dataset"
        df = pd.read_csv(datafiles[ind])
        data = pd.DataFrame(df.dtypes)
        data = data.astype(str)
        data.columns=['Type']
        data = data.Type.replace({'object': 'String','float64': 'Float','int64': 'Int'})
        st.sidebar.table(data)
    else:
        st.sidebar.write('No Dataset selected')
        st.session_state.comand_load = ''
        st.session_state.prompt_load = ''


### Layout Main ###

col1, col2 = st.columns([8,2])

def set_widgets():
    with col2:

        ### Widgets General

        st.text_input("Title", value = plt.gca().get_title(), key="title")
        axes_label = st.expander(label='Axes Label')
        with axes_label:
            st.text_input("Text for x-axis", value = plt.gca().get_xlabel(), key="xaxis")
            st.text_input("Text for y-axis", value = plt.gca().get_ylabel(), key="yaxis")
        axes_limits = st.expander(label='Axes Limits')
        with axes_limits:
            st.number_input("From for x-axis", step=1.0, value=plt.gca().get_xlim()[0], key="xlim_start")
            st.number_input("To for x-axis", step=1.0, value=plt.gca().get_xlim()[1], key="xlim_end")
            st.number_input("From for y-axis", step=1.0, value=plt.gca().get_ylim()[0], key="ylim_start")
            st.number_input("To for y-axis", step=1.0, value=plt.gca().get_ylim()[1], key="ylim_end")

        with open('fig'+ st.session_state.id +'.pickle', 'rb') as f:
            fig = pickle.load(f)

        ### Widgets for Lines

        if plt.gca().lines:
            color_lines = st.expander(label='Line Colors')
            numlines = len(plt.gca().get_lines())
            with color_lines:
                for i in range(numlines):
                    color = plt.gca().get_lines()[i].get_color()
                    color = to_hex(color)
                    st.color_picker('Line '+str(i+1), color, key="linecolor"+str(i))
            style_lines = st.expander(label='Line Style')
            with style_lines:
                for i in range(numlines):
                    lstyle = plt.gca().get_lines()[i].get_linestyle()
                    stylelist = ["-", "--", "-.",":"]
                    if lstyle in stylelist:
                        ind = stylelist.index(lstyle)
                    else:
                        ind = 0
                    st.selectbox("Line "+str(i+1),  ('solid', 'dashed', 'dashdot', 'dotted'), index = ind, key="linestyle"+str(i))
            width_lines = st.expander(label='Line Width')
            with width_lines:
                for i in range(numlines):
                    lwidth = plt.gca().get_lines()[i].get_linewidth()
                    st.number_input("Line "+str(i+1), min_value=0.0, max_value=10.0, step= 1.0, value=lwidth, key="linewidth"+str(i))


            marker_lines = st.expander(label='Marker')
            with marker_lines:
                for i in range(numlines):
                    lmarker = plt.gca().get_lines()[i].get_marker()
                    if lmarker in markersdict.keys():
                        ind = list(markersdict.keys()).index(lmarker)
                    else:
                        ind = 0
                    st.selectbox("Line "+str(i+1),  markersdict.values(), index = ind, key="linemarker"+str(i))

            legend_lines = st.expander(label='Legend')
            with legend_lines:
                if plt.gca().get_legend() != None:
                    vis = plt.gca().get_legend().get_visible()
                else:
                    vis = False
                st.checkbox('Visible', value = vis , key = 'visiblelegend')
                for i in range(numlines):
                    llegend = plt.gca().get_lines()[i].get_label()
                    if llegend.startswith('_'):
                        plt.gca().get_lines()[i].set_label('Line '+str(i))
                        llegend = 'Line '+str(i+1)
                    #print(llegend)
                    st.text_input("Label for line "+str(i+1), value = llegend, key="linelabel"+str(i))


        ### Widgets for Scatterplots #
        if plt.gca().collections:
            color_points = st.expander(label='Point Color Palettes')
            numcolls = len(plt.gca().collections)
            with color_points:
                for i in range(numcolls):
                    pmap = plt.getp(plt.gca().collections[i], 'cmap').name
                    #maplist = ['viridis', 'plasma', 'inferno', 'magma', 'cividis']
                    maplist = plt.colormaps()
                    if pmap in maplist:
                        ind = maplist.index(pmap)
                    else:
                        ind = 0
                    st.selectbox("Points "+str(i+1),  maplist, index = ind, key="pointcolor"+str(i))

        ### Widgets for Barplots
        if plt.gca().containers:
            bar_color = st.expander(label='Color of Bars')
            num_bars = len(plt.gca().containers)
            with bar_color:
                for i in range(num_bars):
                    color = plt.gca().containers[i].patches[0].properties()['facecolor']
                    color = to_hex(color)
                    st.color_picker('Bargroup '+str(i+1), color, key="barcolor"+str(i))

            #legend_bars = st.expander(label='Legend')
            #with legend_bars:
                #if plt.gca().get_legend() != None:
                    #vis = plt.gca().get_legend().get_visible()
                #else:
                    #vis = False
                #st.checkbox('Visible', value = vis , key = 'visiblelegend_bar')
                #for i in range(num_bars):
                    #barlegend = plt.getp(plt.gca(),'legend_handles_labels')[1][i]
                    #st.text_input("Label for Bargroup "+str(i+1), value = barlegend, key="barlabel"+str(i))

def my_exec(script):
    '''Execute a script protected'''
    scriptlist = script.split('\n')
    scriptlist = [scr for scr in scriptlist if not scr.endswith('.show()')]
    for scr in scriptlist[:]:
        try:
            exec(scr)
            print(scr)
        except:
            pass
    return None

### Query Code from getGPT3
def getGPT3():
    on_change=init_widgets()
    if st.session_state.comand_input == '':
        expr = ''
    else:
        prompt = """\"\"\"\n""" + st.session_state.prompt_load + " " + st.session_state.comand_input + """\n\"\"\"\n"""
        print(prompt)
        response = openai.Completion.create(
            engine="davinci-codex",
            prompt=prompt,
            temperature=0,
            max_tokens=500,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
            )
        expr = response.choices[0].text
        #print(exec)
        st.session_state["comand_output"] = expr

    return True



### Create Figure ###

#@st.cache
def create_figure():
    #plt.style.use(st.session_state.style)
    plt.style.use('ggplot')
    plt.rcParams['figure.figsize'] = (10, 5)

    ### Statements from Data and GPT3
    #my_exec(st.session_state.comand_load)
    #print(st.session_state.comand_load)
    if 'comand_output' in st.session_state:
        my_exec(st.session_state.comand_output)


    # Statements from frontend
    ### Set Grid
    my_exec(st.session_state.grid)

    ### Set Axes Labels
    if 'xaxis' in st.session_state:
        my_exec('plt.xlabel(\''+ st.session_state.xaxis +'\')')
    if 'yaxis' in st.session_state:
        my_exec('plt.ylabel(\''+ st.session_state.yaxis +'\')')

    ### Set Limits for the Axes
    if 'xlim_start' in st.session_state and 'xlim_end' in st.session_state:
        plt.xlim(float(st.session_state.xlim_start), float(st.session_state.xlim_end))
    if 'ylim_start' in st.session_state and 'ylim_end' in st.session_state:
        plt.ylim(float(st.session_state.ylim_start), float(st.session_state.ylim_end))

    numcolls = len(plt.gca().collections)
    numlines = len(plt.gca().get_lines())
    num_bars = len(plt.gca().containers)

    ### Set Colors
    for i in range(numlines):
        if 'linecolor'+str(i) in st.session_state:
            exec('plt.gca().get_lines()[i].set_color(\''+ st.session_state['linecolor'+str(i)] +'\')')
            if plt.gca().get_legend() != None:
                exec('plt.gca().get_legend().legendHandles[i].set_color(\''+ st.session_state['linecolor'+str(i)] +'\')')

    ### Set Linestyle
    for i in range(numlines):
        if 'linestyle'+str(i) in st.session_state:
            exec('plt.gca().get_lines()[i].set_linestyle(\''+ st.session_state['linestyle'+str(i)] +'\')')
            if plt.gca().get_legend() != None:
                exec('plt.gca().get_legend().legendHandles[i].set_linestyle(\''+ st.session_state['linestyle'+str(i)] +'\')')

    ### Set Linewidth
    for i in range(numlines):
        if 'linewidth'+str(i) in st.session_state:
            exec('plt.gca().get_lines()[i].set_linewidth(\''+ str(st.session_state['linewidth'+str(i)]) +'\')')

    ### Set Marker
    reversed_markersdict = {value : key for (key, value) in markersdict.items()}
    for i in range(numlines):
        if 'linemarker'+str(i) in st.session_state:
            mark = reversed_markersdict[st.session_state['linemarker'+str(i)]]
            exec('plt.gca().get_lines()[i].set_marker(\''+ mark +'\')')
            if plt.gca().get_legend() != None:
                exec('plt.gca().get_legend().legendHandles[i].set_marker(\''+ mark +'\')')

    ### Set legend
    for i in range(numlines):
        if 'linelabel'+str(i) in st.session_state:
            exec('plt.gca().get_lines()[i].set_label(\''+ st.session_state['linelabel'+str(i)] +'\')')
            plt.legend()

    if 'visiblelegend' in st.session_state:
        if st.session_state.visiblelegend:
            if plt.gca().get_legend() != None:
                plt.gca().get_legend().set_visible(True)
        else:
            if plt.gca().get_legend() != None:
                plt.gca().get_legend().set_visible(False)

############## Scatterplots #####

    ### Set Colormap
    for i in range(numcolls):
        if 'pointcolor'+str(i) in st.session_state:
            plt.setp(plt.gca().collections[i], cmap=plt.get_cmap(st.session_state['pointcolor'+str(i)]))
        #plt.getp(plt.gca().collections[i], 'cmap').name

############## Barcharts ##########

    ### Set Colors of Bargroups
    for i in range(num_bars):
        if plt.gca().get_legend() != None:
            plt.gca().get_legend().set_visible(False)
        if 'barcolor'+str(i) in st.session_state:
            for j in range(len(plt.gca().containers[i].patches)):
                plt.setp(plt.gca().containers[i].patches[j], facecolor = st.session_state['barcolor'+str(i)])
            #exec('plt.gca().get_lines()[i].set_color(\''+ st.session_state['linecolor'+str(i)] +'\')')
            #if plt.gca().get_legend() != None:
                #exec('plt.gca().get_legend().legendHandles[i].set_color(\''+ st.session_state['linecolor'+str(i)] +'\')')

    ### Set legend for Bars
    #for i in range(num_bars):
        #if 'barlabel'+str(i) in st.session_state:
            #plt.gca().properties()['legend_handles_labels'][1][i] = st.session_state['barlabel'+str(i)]
            #exec('plt.gca().get_lines()[i].set_label(\''+ st.session_state['linelabel'+str(i)] +'\')')
            #plt.legend()

    #if 'visiblelegend_bar' in st.session_state:
        #if st.session_state.visiblelegend_bar:
            #if plt.gca().get_legend() != None:
                #plt.gca().get_legend().set_visible(True)
        #else:
            #if plt.gca().get_legend() != None:
                #plt.gca().get_legend().set_visible(False)

######## Set Title
    if 'title' in st.session_state:
        my_exec('plt.gca().set_title(\''+ st.session_state.title +'\')')

    fig = plt.gcf()
    with open('fig'+ st.session_state.id +'.pickle', 'wb') as f: # should be 'wb' rather than 'w'
        pickle.dump(fig, f)

    return fig


with col1:
    #st.write(st.session_state)
    st.header('Create Charts with Commands in Natural Language')
    demo_video = st.expander(label='Tutorial Video')
    with demo_video:
        #video_file = open('NLP2Chart.mp4', 'rb')
        #video_bytes = video_file.read()
        st.video(data="https://youtu.be/UiCSczhslAs")
    st.text_area("Advise the system", key="comand_input", on_change=getGPT3,
        help="Examples: \n Plot a sinus function from -4 pi to 4 pi; \n Make an array of 400 random numbers and plot a horizontal histogram; \n plot sum of total_cases grouped by location as bar chart (COVID19 Data)")
    fig = create_figure()
    st.pyplot(fig=fig)

set_widgets()

### Export Figures

st.sidebar.markdown('### Export ###')

with open('fig'+ st.session_state.id +'.pickle', 'rb') as f:
    fig = pickle.load(f)
fig.savefig('figure_export.png', dpi=fig.dpi)
mpld3.save_html(fig,'figure_export.html')
with open('figure_export.png', 'rb') as f:
   st.sidebar.download_button('Download PNG', f, file_name='figure_export.png')
with open('figure_export.html', 'rb') as f:
   st.sidebar.download_button('Download HTML', f, file_name='figure_export.html')
