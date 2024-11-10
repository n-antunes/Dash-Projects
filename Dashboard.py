import pandas as pd
import plotly.express as px
import streamlit as st
import random
import locale
import io

locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

arquivo = 'XXX.csv'

#Configurando a Página Inicial
st.set_page_config(
    page_title='Informações Gerais',
    page_icon=None,
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items=None
    )

# Função para carregar o arquivo CSV, com tratamento de exceção
def carregar_arquivo(arquivo):
    """Função para ler o arquivo CSV e tratar erros caso o arquivo não exista ou esteja corrompido."""
    try:
        bd = pd.read_csv(arquivo, encoding='UTF-8')
    except Exception as e:
        st.error(f"Erro ao ler o arquivo: {e}")
        st.stop()


#Lendo Arquivo da Base de Dados
bd['Pedido'] = bd['Pedido'].astype(str)
bd['Data de Entrega'] = pd.to_datetime(bd['Data de Entrega'], format='%d/%m/%Y', errors='coerce')
bd['Data Finalização'] = pd.to_datetime(bd['Data Finalização'], format='%d/%m/%Y', errors='coerce')


#Iniciando Função Principal
def home():
    """Função principal que exibe as informações gerais e gráficos interativos no Streamlit."""
    st.title('Informações Gerais')

    #Filtrando informações relevantes
    bd_geral = bd[['Pedido', 'Cliente', 'SKU', 'Item', 'Cor', 'Tamanho', 'Quantidade', 'Categoria', 'Data de Entrega', 'Finalizado', 'Data Finalização']]
    #Garante que se o valor passado em 'Finalizado' for uma string ela sempre será em maiúscula
    bd_geral['Finalizado'] = bd_geral['Finalizado'].apply(lambda x: x.upper() if isinstance(x, str) else x)
    bd_geral = bd_geral.query('Finalizado != "SIM" & Finalizado != "CANCELADO"')
    bd_geral.sort_values(by=['Data de Entrega'], inplace=True)

    #Filtrando intervalo de data de interesse#
    data_inicio = st.date_input("Selecione a Data Inicial de Entrega", value=bd_geral['Data de Entrega'].min(),
                                min_value=bd_geral['Data de Entrega'].min(),
                                max_value=bd_geral['Data de Entrega'].max(),
                                format="DD/MM/YYYY")
    data_fim = st.date_input("Selecione a Data Final de Entrega", value=bd_geral['Data de Entrega'].max(),
                             min_value=bd_geral['Data de Entrega'].min(),
                             max_value=bd_geral['Data de Entrega'].max(),
                             format="DD/MM/YYYY")

    data_inicio = pd.to_datetime(data_inicio, format='%d/%m/%Y', errors="coerce")
    data_fim = pd.to_datetime(data_fim, format='%d/%m/%Y', errors="coerce")
    # Garante que a exibição do gráfico não dê errado
    if data_inicio > data_fim:
        st.warning('A Data Inicial não pode ser Maior que a Final')
        data_inicio = data_fim
        data_filtrada = bd_geral[
            (bd_geral['Data de Entrega'] >= data_inicio) & (bd_geral['Data de Entrega'] <= data_fim)]
    else:
        # Filtrando os dados com base nas datas selecionadas
        data_filtrada = bd_geral[
            (bd_geral['Data de Entrega'] >= data_inicio) & (bd_geral['Data de Entrega'] <= data_fim)]

    #Retornando novas informações com base na data de interesse#
    quantidade_pedidos = int(len(data_filtrada['Pedido'].unique()))
    data_filtrada['Quantidade'] = data_filtrada['Quantidade'].astype(int)
    data_filtrada['Finalizado'] = data_filtrada['Finalizado'].fillna(0).astype(int)
    data_filtrada['Qtd. Falta'] = data_filtrada['Quantidade'] - data_filtrada['Finalizado']

    #Somando e formatando valores#
    quantidade_pecas = int(data_filtrada['Qtd. Falta'].sum())
    formatado_valor = '{:,.0f}'.format(quantidade_pedidos).replace(',', '.')
    formatado_pcs = '{:,.0f}'.format(quantidade_pecas).replace(',', '.')
    st.subheader('Quantidade de Pedidos: {}'.format(formatado_valor))
    st.subheader('Quantidade de Peças: {}'.format(formatado_pcs))
    grouped_data = data_filtrada.groupby(['Data de Entrega', 'Categoria'])['Qtd. Falta'].sum().unstack(fill_value=0).reset_index()

    #Gerando gráfico com as informações e quantidades filtradas#
    if quantidade_pedidos == 0:
        st.warning('Não Existem Pedidos para Entregar na Data Selecionada')

    else:
        x_values = grouped_data.columns[0]
        y_values = grouped_data.columns[1:]

        fig_px = px.bar(
            grouped_data,
            x=x_values,
            y=y_values,
            title="Quantidade de Peças para Entregar por Dia",
            width=1200,
            height=500,
            color_discrete_map={
                'Cat1': 'royalblue',
                'Cat2': 'red',
                'Cat3': 'navy',
                'Cat4': 'green',
                'Cat5': 'gold',
                'Cat6': 'chocolate',
            }
        )

        #Atualizar layout com títulos e legendas#
        fig_px.update_layout(
            xaxis_title="Data",
            yaxis_title="Quantidade",
            legend_title="Categorias",
            title="Peças a Entregar por Categoria"
        )

        #Exibindo o gráfico no Streamlit#
        st.plotly_chart(fig_px, use_container_width=True)
        
        #Retornando informações para download#
        relatorio = data_filtrada.groupby(['Pedido', 'Cliente', 'SKU', 'Cor', 'Produto', 'Categoria', 'Data de Entrega'])['Qtd. Falta'].sum().reset_index()
        relatorio = relatorio.sort_values(by=['Data de Entrega', 'Cliente', 'Pedido', 'SKU', 'Cor'])
        relatorio['Data de Entrega'] = pd.to_datetime(relatorio['Data de Entrega'], format='%d/%m/%Y', errors='coerce')
        relatorio['Data de Entrega'] = relatorio['Data de Entrega'].apply(lambda x: x.strftime('%d/%m/%Y'))
	
	#Criando uma base para cada categoria de SKU#
        bd_Cat1 = relatorio[relatorio['Categoria'] == 'Cat1']
        bd_Cat2 = relatorio[relatorio['Categoria'] == 'Cat2']
        bd_Cat3 = relatorio[relatorio['Categoria'] == 'Cat3']
        bd_Cat4 = relatorio[relatorio['Categoria'] == 'Cat4']
        bd_Cat5 = relatorio[relatorio['Categoria'] == 'Cat5']
        bd_Cat6 = relatorio[relatorio['Categoria'] == 'Cat6']

    #Criando a função para download dos relatórios# 
    def gerando_relatorio(relatorio, name):
    """Gera os arquivos para serem baixados no botão do streamlit"""
        def convert_df(relatorio):
            return relatorio.to_csv(index=False).encode("utf-8")

        def convert_df_xlsx(relatorio):
            # Usar um buffer em memória para salvar o arquivo Excel
            output = io.BytesIO()
            relatorio.to_excel(output, index=False, engine='openpyxl')
            output.seek(0)  # Rewind the buffer
            return output

        # Valores para o random#
        start = 1
        stop = int(1e20)

        csv1 = convert_df(relatorio)
        excel = convert_df_xlsx(relatorio)

        st.download_button(
            label=f"Relatório {name}",
            data=csv1,
            key=random.randrange(start, stop),
            file_name=f"Relatório {name}.csv",
            mime="text/csv",
        )

        st.download_button(
            label=f"{name} Excel",
            data=excel,
            key=random.randrange(start, stop),
            file_name=f"Relatório {name}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

        quantidade_pecas = relatorio['Qtd. Falta'].astype(int).sum()
        st.write(f'{name}: {quantidade_pecas}')

    # Criando os botões para download para cada categoria
    col1, col2, col3, col4, col5, col6, col7 = st.columns(7)

    with col1:
        gerando_relatorio(relatorio, 'Geral')

    with col2:
        gerando_relatorio(bd_Cat4, 'Cat4')

    with col3:
        gerando_relatorio(bd_Cat3, 'Cat3')

    with col4:
        gerando_relatorio(bd_Cat1, 'Cat1')

    with col5:
        gerando_relatorio(bd_Cat6, 'Cat6')

    with col6:
        gerando_relatorio(bd_Cat5, 'Cat5')

    with col7:
        gerando_relatorio(bd_Cat2, 'Cat2')

if __name__ == "__main__":
	home()
