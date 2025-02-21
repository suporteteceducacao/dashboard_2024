import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os

# Configuração da página Streamlit
st.set_page_config(
    page_title="Dashboard Escolar",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Adicionando o logotipo na barra lateral
#logo_url = 'img/https://raw.githubusercontent.com/suporteteceducacao/dashboard_2024/main/img/logo_2021.png''
#with st.sidebar:
    #st.image(logo_url, width=250)

# Título principal
title_text = "📊 Dashboard de Resultados Escolares - Avaliações Externas (CNCA, AVALIE.CE e PNRA)"
st.title(title_text)
st.markdown("Bem-vindo ao sistema de acesso aos resultados escolares.")

# Função para carregar os dados
@st.cache_data
def load_data(file_path):
    try:
        df = pd.read_excel(file_path, dtype=str)  # Garantir que os dados sejam carregados corretamente
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        st.error(f"Erro ao carregar {file_path}: {str(e)}")
        return None

# Carregar planilhas
df_login = load_data('https://raw.githubusercontent.com/suporteteceducacao/dashboard_2024/main/xls/senhas_acesso_2.xlsx')
df_resultados = load_data('')

if df_login is None or df_resultados is None:
    st.stop()

# Limpeza de dados
df_login['INEP'] = df_login['INEP'].astype(str).str.strip()
df_login['SENHA'] = df_login['SENHA'].astype(str).str.strip()
df_login['Escola'] = df_login['Escola'].astype(str).str.strip()

df_resultados['INEP'] = df_resultados['INEP'].astype(str).str.strip()
df_resultados['Escola'] = df_resultados['Escola'].astype(str).str.strip()

# Credenciais da senha mestra
SENHA_MESTRE = '8240'
INEP_MESTRE = '2307650'

# Inicializar variáveis de sessão
if 'login_success' not in st.session_state:
    st.session_state.login_success = False
if 'escola_logada' not in st.session_state:
    st.session_state.escola_logada = None

# Barra lateral de login
with st.sidebar:
    st.header("🔒 Acesso Restrito")
    with st.form(key='login_form'):
        inep = st.text_input('INEP').strip()
        senha = st.text_input('SENHA', type='password').strip()
        login_button = st.form_submit_button('Login')

# Lógica de login
if login_button:
    if inep == INEP_MESTRE and senha == SENHA_MESTRE:
        st.session_state.login_success = True
        st.session_state.escola_logada = 'MARACANAÚ'
        st.success('Login realizado com sucesso como administrador!')
    else:
        usuario = df_login[df_login['INEP'] == inep]
        if not usuario.empty:
            senha_correta = usuario['SENHA'].values[0]
            if senha == senha_correta:
                st.session_state.login_success = True
                st.session_state.escola_logada = usuario['Escola'].values[0]
                st.success(f'Login realizado com sucesso na escola {st.session_state.escola_logada}!')
            else:
                st.error('Senha incorreta.')
        else:
            st.error('INEP não encontrado.')

# Exibir conteúdo após login
if st.session_state.login_success:
    # Define df_escola com base no tipo de usuário logado
    if st.session_state.escola_logada == 'MARACANAÚ':
        df_escola = df_resultados  # Mostra todos os resultados para o admin
    else:
        df_escola = df_resultados[df_resultados['Escola'] == st.session_state.escola_logada]  # Mostra resultados da escola específica

    if df_escola.empty:
        st.warning("Nenhum dado encontrado para esta escola.")
    else:
        
        # Criar abas
        tab1, tab2 = st.tabs(["Dados Estatísticos", "Gráficos"])
        
        with tab1:
            # Mostrar todos os resultados da escola logada
            st.markdown(f"<h3>Bem-vindo escola <span style='color: blue;'>{st.session_state.escola_logada}</span></h1>", unsafe_allow_html=True)

            # Exibir todos os resultados
            st.subheader("Tabela de Resultados")
            st.dataframe(df_escola, use_container_width=True)

            # Converter coluna 'Acerto Total' para numérico (corrigindo o erro)
            try:
                df_escola['Acerto Total'] = pd.to_numeric(df_escola['Acerto Total'], errors='coerce')
            except KeyError:
                st.error("A coluna 'Acerto Total' não foi encontrada nos dados.")
                st.stop()

            # Cálculo de variações para 'Acerto Total'
            # Agrupa por 'Escola', 'Etapa', 'Componente Curricular' e 'Modalidade'
            df_variacoes = df_escola.sort_values(by=['Escola', 'Etapa', 'Componente Curricular', 'Modalidade', 'Ciclo'])
            
            # Calcular diferenças e variações apenas se houver dados suficientes
            if len(df_variacoes) > 1:  # Verifica se há mais de uma linha para calcular diferenças
                # Modifica o groupby para incluir 'Modalidade' e 'Ciclo'
                df_variacoes['Diferença Acerto Total'] = df_variacoes.groupby(['Escola', 'Etapa', 'Componente Curricular', 'Modalidade'])['Acerto Total'].diff()
                df_variacoes['Variação Acerto Total (%)'] = df_variacoes.groupby(['Escola', 'Etapa', 'Componente Curricular', 'Modalidade'])['Acerto Total'].pct_change() * 100
                
                # Formatação das diferenças e variações com cores e setas
                def color_code(value):
                    if pd.isna(value):
                        return ""  # Retorna string vazia se o valor for NaN
                    if value < 0:
                        return f"<span style='color:red;'>{value:.2f} &#8595;</span>"  # Vermelho com seta para baixo
                    elif value > 0:
                        return f"<span style='color:green;'>{value:.2f} &#8593;</span>"  # Verde com seta para cima
                    else:
                        return f"{value:.2f}"  # Sem formatação para zero

                def format_percentage(value):
                    if pd.isna(value):
                        return ""  # Retorna string vazia se o valor for NaN
                    if value < 0:
                        return f"<span style='color:red;'>{value:.2f}% &#8595;</span>"  # Vermelho com seta para baixo
                    elif value > 0:
                        return f"<span style='color:green;'>{value:.2f}% &#8593;</span>"  # Verde com seta para cima
                    else:
                        return f"{value:.2f}%"  # Sem formatação para zero

                # Aplicar formatação às colunas de diferença e variação percentual
                formatted_df_variacoes = df_variacoes.copy()
                formatted_df_variacoes['Diferença Acerto Total'] = formatted_df_variacoes['Diferença Acerto Total'].apply(lambda x: color_code(x) if pd.notnull(x) else "")
                formatted_df_variacoes['Variação Acerto Total (%)'] = formatted_df_variacoes['Variação Acerto Total (%)'].apply(lambda x: format_percentage(x) if pd.notnull(x) else "")
                
                # Selecionar apenas as colunas desejadas para exibição na tabela final
                columns_to_display = ['Escola', 'Componente Curricular', 'Etapa', 'Acerto Total', 'Modalidade', 'Ciclo', 
                                    'Diferença Acerto Total', 'Variação Acerto Total (%)']
                formatted_df_variacoes_display = formatted_df_variacoes[columns_to_display]

                # Filtros adicionais (apenas se senha mestra estiver logada)
                if st.session_state.escola_logada == "MARACANAÚ":
                    escolas_options = formatted_df_variacoes_display["Escola"].unique()
                    modalidades_options = formatted_df_variacoes_display["Modalidade"].unique()

                    selected_escolas = st.multiselect(
                        "Selecione as Escolas:",
                        options=escolas_options,
                        default=escolas_options.tolist()
                    )

                    selected_modalidades = st.multiselect(
                        "Selecione as Modalidades:",
                        options=modalidades_options,
                        default=modalidades_options.tolist()
                    )

                    formatted_df_variacoes_display = formatted_df_variacoes_display[
                        formatted_df_variacoes_display["Escola"].isin(selected_escolas) &
                        formatted_df_variacoes_display["Modalidade"].isin(selected_modalidades)
                    ]

                componentes_curriculares_options = formatted_df_variacoes_display["Componente Curricular"].unique()
                etapas_options = formatted_df_variacoes_display["Etapa"].unique()
                modalidades_options = formatted_df_variacoes_display["Modalidade"].unique()

                selected_componentes_curriculares = st.multiselect(
                    "Selecione os Componentes Curriculares:",
                    options=componentes_curriculares_options,
                    default=componentes_curriculares_options.tolist()
                )

                selected_etapas = st.multiselect(
                    "Selecione as Etapas:",
                    options=etapas_options,
                    default=etapas_options.tolist()
                )

                selected_modalidades = st.multiselect(
                        "Selecione as Modalidades:",
                        options=modalidades_options,
                        default=modalidades_options.tolist()
                    )

                filtered_df_variacoes_display = formatted_df_variacoes_display[
                    (formatted_df_variacoes_display["Componente Curricular"].isin(selected_componentes_curriculares)) &
                    (formatted_df_variacoes_display["Etapa"].isin(selected_etapas)) &
                    (formatted_df_variacoes_display["Modalidade"].isin(selected_modalidades))
                ]

                # Exibir resultados filtrados em HTML
                if filtered_df_variacoes_display.empty:
                    st.warning("Nenhum dado encontrado com os filtros selecionados.")
                else:
                    st.subheader("Tabela de Diferenças e Variações do Acerto Total")
                    st.markdown(filtered_df_variacoes_display.to_html(escape=False, na_rep=''), unsafe_allow_html=True)

                    # Botão para baixar a tabela filtrada em Excel (nome curto corrigido)
                    if st.button("Baixar Excel com Diferenças"):
                        output_file_filtered = "variacoes.xlsx"
                        with pd.ExcelWriter(output_file_filtered) as writer:
                            filtered_df_variacoes_display.to_excel(writer, index=False, sheet_name="Variacoes")
                        with open(output_file_filtered, "rb") as file:
                            btn_filtered = st.download_button(
                                label="Clique aqui para baixar",
                                data=file,
                                file_name=output_file_filtered,
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
            else:
                st.warning("Não há dados suficientes para calcular diferenças e variações.")

        with tab2:
            # Mostrar todos os resultados da escola logada
            st.markdown(f"<h3>Bem-vindo escola <span style='color: blue;'>{st.session_state.escola_logada}</span></h1>", unsafe_allow_html=True)

            st.header("Gráficos de Desempenho")
                        
            # Verificar se as colunas necessárias existem
            required_columns = ['Defasagem', 'intermediario', 'adequado', 'Acerto Total', 'Etapa', 'Componente Curricular', 'Ciclo', 'Modalidade']
            if all(column in df_escola.columns for column in required_columns):
                # Converter colunas para numérico
                df_escola['Defasagem'] = pd.to_numeric(df_escola['Defasagem'], errors='coerce')
                df_escola['intermediario'] = pd.to_numeric(df_escola['intermediario'], errors='coerce')
                df_escola['adequado'] = pd.to_numeric(df_escola['adequado'], errors='coerce')
                df_escola['Acerto Total'] = pd.to_numeric(df_escola['Acerto Total'], errors='coerce')

                # Selecionar Etapa, Componente Curricular e Modalidade
                etapas = df_escola['Etapa'].unique()
                componentes_curriculares = df_escola['Componente Curricular'].unique()
                modalidades = df_escola['Modalidade'].unique()

                selected_etapa = st.selectbox("Selecione a Etapa:", etapas)
                selected_componente = st.selectbox("Selecione o Componente Curricular:", componentes_curriculares)
                selected_modalidade = st.selectbox("Selecione a Modalidade:", modalidades)

                # Filtrar dados
                filtered_data = df_escola[
                    (df_escola['Etapa'] == selected_etapa) & 
                    (df_escola['Componente Curricular'] == selected_componente) & 
                    (df_escola['Modalidade'] == selected_modalidade)
                ]

                if not filtered_data.empty:
                    # Gráfico de Barras Empilhadas 100% (Horizontal)
                    st.subheader("Gráfico de Percentual Médio por Faixa de Aprendizagem")
                    fig, ax = plt.subplots(figsize=(8, 3))  # Tamanho menor para melhor visualização
                    
                    # Calcular proporções para cada categoria
                    total = filtered_data[['Defasagem', 'intermediario', 'adequado']].sum(axis=1)
                    filtered_data['Defasagem_pct'] = filtered_data['Defasagem'] / total * 100
                    filtered_data['intermediario_pct'] = filtered_data['intermediario'] / total * 100
                    filtered_data['adequado_pct'] = filtered_data['adequado'] / total * 100

                    # Plotar gráfico de barras empilhadas 100% (horizontal)
                    left = np.zeros(len(filtered_data))
                    for col, color in zip(['Defasagem_pct', 'intermediario_pct', 'adequado_pct'], ['yellow', 'lightgreen', 'darkgreen']):
                        ax.barh(filtered_data['Ciclo'], filtered_data[col], left=left, label=col.split('_')[0], color=color)
                        left += filtered_data[col]

                    # Adicionar rótulos com os valores
                    for i, ciclo in enumerate(filtered_data['Ciclo']):
                        ax.text(filtered_data['Defasagem_pct'].iloc[i] / 2, i, f"{filtered_data['Defasagem_pct'].iloc[i]:.1f}%", ha='center', va='center')
                        ax.text(filtered_data['Defasagem_pct'].iloc[i] + filtered_data['intermediario_pct'].iloc[i] / 2, i, f"{filtered_data['intermediario_pct'].iloc[i]:.1f}%", ha='center', va='center')
                        ax.text(filtered_data['Defasagem_pct'].iloc[i] + filtered_data['intermediario_pct'].iloc[i] + filtered_data['adequado_pct'].iloc[i] / 2, i, f"{filtered_data['adequado_pct'].iloc[i]:.1f}%", ha='center', va='center')

                    ax.set_title(f"Proporção de Desempenho por Ciclo - {selected_etapa} - {selected_componente} - {selected_modalidade}")
                    ax.set_xlabel("Proporção (%)")
                    ax.set_ylabel("Ciclo")
                    ax.legend(title="Categoria")

                    # Ajustar a legenda
                    ax.legend(title="Categoria", fontsize='small', bbox_to_anchor=(1.05, 1), loc='upper left')

                    st.pyplot(fig)

                    # Gráfico de Barras Verticais para Acerto Total
                    st.subheader("Gráfico de Desempenho Médio")
                    fig, ax = plt.subplots(figsize=(8, 4))  # Tamanho menor para melhor visualização
                    sns.barplot(data=filtered_data, x='Ciclo', y='Acerto Total', color='blue', ax=ax)
                    
                    # Adicionar rótulos com os valores
                    for i, ciclo in enumerate(filtered_data['Ciclo']):
                        ax.text(i, filtered_data['Acerto Total'].iloc[i], f"{filtered_data['Acerto Total'].iloc[i]:.1f}", ha='center', va='bottom')

                    ax.set_title(f"Acerto Total por Ciclo - {selected_etapa} - {selected_componente} - {selected_modalidade}")
                    ax.set_xlabel("Ciclo")
                    ax.set_ylabel("Acerto Total")
                    st.pyplot(fig)
                else:
                    st.warning("Nenhum dado encontrado para os filtros selecionados.")
            else:
                st.error(f"As colunas necessárias para os gráficos não foram encontradas nos dados. Colunas esperadas: {required_columns}")

    # Botão de logout (corrigido para limpar sessão imediatamente)
    if st.sidebar.button("Sair"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.experimental_rerun()
else:
    st.info("Por favor, insira suas credenciais para acessar os resultados.")
