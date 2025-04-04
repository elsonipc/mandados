import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
import tempfile
import base64
import hashlib
from PIL import Image
import io
import os

# Configuração inicial
st.set_page_config(page_title="Analista de Mandados de Prisão", layout="wide")

# Função para formatar data
def formatar_data(data):
    try:
        if pd.isna(data):
            return "N/A"
        if isinstance(data, str):
            data = pd.to_datetime(data)
        return data.strftime('%d/%m/%Y')
    except:
        return "N/A"

# Função para gerar ID único
def generate_unique_id(processo, nome):
    unique_str = f"{processo}_{nome}"
    return hashlib.md5(unique_str.encode()).hexdigest()

# Função para carregar os dados
@st.cache_data
def load_data(file):
    try:
        df = pd.read_excel(file)
        df.columns = [col.strip() for col in df.columns]
        
        # Verificar e padronizar o nome da coluna de observações
        obs_col = next((col for col in df.columns if 'observa' in col.lower()), 'observações')
        if obs_col not in df.columns:
            df['observações'] = ''
        
        # Criar coluna de identificação única
        df['unique_id'] = df.apply(lambda x: generate_unique_id(x['Processo'], x['Nome']), axis=1)
        
        # Criar coluna para exibição no dropdown
        df['display_name'] = df['Nome'] + " (" + df['Processo'] + ")"
        
        # Formatando a coluna de nascimento
        if 'Nascimento' in df.columns:
            df['Nascimento'] = df['Nascimento'].apply(formatar_data)
        
        # Ordenar por nome (ordem alfabética)
        df = df.sort_values(by='Nome')
        
        return df, obs_col
    except Exception as e:
        st.error(f"Erro ao carregar o arquivo: {e}")
        return None, None

# Função para adicionar texto justificado ao PDF
def add_justified_text(pdf, text, x, y, w, h):
    pdf.set_xy(x, y)
    pdf.set_font("Arial", size=10)
    
    # Divide o texto em linhas
    lines = []
    for line in text.split('\n'):
        words = line.split(' ')
        current_line = words[0]
        
        for word in words[1:]:
            if pdf.get_string_width(current_line + ' ' + word) < w:
                current_line += ' ' + word
            else:
                lines.append(current_line)
                current_line = word
        lines.append(current_line)
    
    # Escreve cada linha
    for line in lines:
        pdf.cell(w, h, line, ln=1, align='L')

# Função para criar PDF individual
def create_pdf(record, image_data=None):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Cabeçalho
    pdf.cell(200, 10, txt="RELATÓRIO INDIVIDUAL DE MANDADO DE PRISÃO", ln=1, align='C')
    pdf.cell(200, 10, txt=f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=1, align='C')
    pdf.ln(10)
    
    # Se houver imagem, adiciona ao lado dos dados
    if image_data:
        try:
            # Salva a imagem em um arquivo temporário
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_img_file:
                tmp_img_file.write(image_data)
                tmp_img_path = tmp_img_file.name
            
            # Lê a imagem para obter dimensões
            img = Image.open(io.BytesIO(image_data))
            
            # Define tamanho máximo para a imagem (40mm de largura)
            max_width = 40
            width_percent = (max_width / float(img.size[0]))
            height_size = int((float(img.size[1]) * float(width_percent)))
            
            # Adiciona a imagem ao PDF
            pdf.image(tmp_img_path, x=160, y=30, w=max_width, h=height_size)
            
            # Remove o arquivo temporário
            os.unlink(tmp_img_path)
        except Exception as e:
            st.error(f"Erro ao processar imagem: {e}")
    
    # Dados do processo
    pdf.set_font("Arial", 'B', size=12)
    pdf.cell(200, 10, txt="DADOS DO PROCESSO:", ln=1)
    pdf.set_font("Arial", size=10)
    
    pdf.cell(100, 8, txt=f"Processo: {record['Processo']}", ln=1)
    pdf.cell(100, 8, txt=f"Nome: {record['Nome']}", ln=1)
    pdf.cell(100, 8, txt=f"Mãe: {record['Mãe']}", ln=1)
    pdf.cell(100, 8, txt=f"Nascimento: {record['Nascimento']}", ln=1)
    pdf.cell(100, 8, txt=f"CPF: {record['CPF']}", ln=1)
    pdf.cell(100, 8, txt=f"Endereço: {record['Rua']}, {record['Casa']} - {record['Bairro']}", ln=1)
    pdf.cell(100, 8, txt=f"Regime: {record['Regime']}", ln=1)
    pdf.cell(100, 8, txt=f"Espécie: {record['Espécie']}", ln=1)
    pdf.cell(100, 8, txt=f"Tipificação: {record['Tipificação']}", ln=1)
    
    # Observações em vermelho
    pdf.set_font("Arial", 'B', size=12)
    pdf.set_text_color(255, 0, 0)  # Vermelho
    pdf.cell(200, 10, txt="OBSERVAÇÕES:", ln=1)
    pdf.set_font("Arial", size=10)
    
    # Adiciona texto justificado
    add_justified_text(pdf, record['Observações'], 10, pdf.get_y(), 190, 6)
    
    # Resetar cor para preto
    pdf.set_text_color(0, 0, 0)
    
    # Rodapé
    pdf.ln(10)
    pdf.set_font("Arial", 'I', size=8)
    pdf.cell(200, 5, txt="Documento gerado automaticamente pelo Analista de Mandados de Prisão", ln=1, align='C')
    
    return pdf

# Função para criar PDF completo
def create_full_pdf(records):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Cabeçalho
    pdf.cell(200, 10, txt="RELATÓRIO COMPLETO DE MANDADOS DE PRISÃO", ln=1, align='C')
    pdf.cell(200, 10, txt=f"Gerado por IPC-Elson Brito, em: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=1, align='C')
    pdf.ln(10)
    
    for idx, record in enumerate(records, 1):
        # Dados do processo
        pdf.set_font("Arial", 'B', size=12)
        pdf.cell(200, 10, txt=f"Processo {idx}: {record['Processo']} - {record['Nome']}", ln=1)
        pdf.set_font("Arial", size=10)
        
        # Adicionar dados principais
        pdf.cell(100, 8, txt=f"Mãe: {record['Mãe']}", ln=1)
        pdf.cell(100, 8, txt=f"Nascimento: {record['Nascimento']}", ln=1)
        pdf.cell(100, 8, txt=f"CPF: {record['CPF']}", ln=1)
        pdf.cell(100, 8, txt=f"Endereço: {record['Rua']}, {record['Casa']} - {record['Bairro']}", ln=1)
        pdf.cell(100, 8, txt=f"Regime: {record['Regime']}", ln=1)
        pdf.cell(100, 8, txt=f"Espécie: {record['Espécie']}", ln=1)
        pdf.cell(100, 8, txt=f"Tipificação: {record['Tipificação']}", ln=1)
        
        # Observações em vermelho
        pdf.set_font("Arial", 'B', size=10)
        pdf.set_text_color(255, 0, 0)  # Vermelho
        pdf.cell(200, 8, txt="Observações:", ln=1)
        pdf.set_font("Arial", size=10)
        
        # Adicionar observações com quebra de linha e justificado
        add_justified_text(pdf, record['Observações'], 10, pdf.get_y(), 190, 6)
        
        # Resetar cor para preto
        pdf.set_text_color(0, 0, 0)
        
        pdf.ln(5)
        pdf.cell(200, 1, txt="-"*80, ln=1)
        pdf.ln(5)
    
    # Rodapé
    pdf.ln(10)
    pdf.set_font("Arial", 'I', size=8)
    pdf.cell(200, 5, txt=f"Documento gerado automaticamente - Total de Mandados: {len(records)}", ln=1, align='C')
    
    return pdf

# Interface do Streamlit
st.title("Analista de Mandados de Prisão")

uploaded_file = st.file_uploader("Carregue o arquivo Excel", type=["xlsx"])

if uploaded_file is not None:
    df, obs_col = load_data(uploaded_file)
    
    if df is not None and obs_col is not None:
        # Inicializar session_state para armazenar observações, imagens e modo de edição
        if 'observacoes' not in st.session_state:
            st.session_state.observacoes = {uid: obs for uid, obs in zip(df['unique_id'], df[obs_col].fillna(''))}
        if 'imagens' not in st.session_state:
            st.session_state.imagens = {uid: None for uid in df['unique_id']}
        if 'edit_mode' not in st.session_state:
            st.session_state.edit_mode = {uid: False for uid in df['unique_id']}
        
        # Lista suspensa com nomes e processos
        selected_display = st.selectbox(
            "Selecione um processo:",
            options=df['display_name'].unique(),
            format_func=lambda x: x
        )
        
        # Obter registro selecionado
        selected_record = df[df['display_name'] == selected_display].iloc[0].to_dict()
        unique_id = selected_record['unique_id']
        
        # Mostrar detalhes do registro selecionado
        st.subheader("Detalhes do Processo")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Processo:** {selected_record['Processo']}")
            st.write(f"**Nome:** {selected_record['Nome']}")
            st.write(f"**Mãe:** {selected_record['Mãe']}")
            st.write(f"**Nascimento:** {selected_record['Nascimento']}")
            st.write(f"**CPF:** {selected_record['CPF']}")
        
        with col2:
            st.write(f"**Endereço:** {selected_record['Rua']}, {selected_record['Casa']}")
            st.write(f"**Bairro:** {selected_record['Bairro']}")
            st.write(f"**Regime:** {selected_record['Regime']}")
            st.write(f"**Espécie:** {selected_record['Espécie']}")
            st.write(f"**Tipificação:** {selected_record['Tipificação']}")
        
        # Upload de imagem
        uploaded_image = st.file_uploader(
            "Adicionar foto (JPEG ou PNG)", 
            type=["jpg", "jpeg", "png"],
            key=f"img_upload_{unique_id}"
        )
        
        if uploaded_image is not None:
            # Armazena a imagem em bytes no session_state
            st.session_state.imagens[unique_id] = uploaded_image.read()
            st.image(st.session_state.imagens[unique_id], caption="Foto carregada", width=200)
        elif st.session_state.imagens.get(unique_id):
            st.image(st.session_state.imagens[unique_id], caption="Foto carregada anteriormente", width=200)
        
        # Área para observações com botões de editar/salvar
        st.subheader("Observações")
        
        if st.session_state.edit_mode.get(unique_id, False):
            # Modo de edição
            new_obs = st.text_area(
                "Editar observações:",
                value=st.session_state.observacoes.get(unique_id, ""),
                key=f"obs_edit_{unique_id}",
                height=200
            )
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 Salvar", key=f"save_{unique_id}"):
                    st.session_state.observacoes[unique_id] = new_obs
                    st.session_state.edit_mode[unique_id] = False
                    # Atualizar a coluna no DataFrame
                    df.loc[df['unique_id'] == unique_id, obs_col] = new_obs
                    st.success("Observações salvas com sucesso!")
                    st.rerun()
            with col2:
                if st.button("❌ Cancelar", key=f"cancel_{unique_id}"):
                    st.session_state.edit_mode[unique_id] = False
                    st.rerun()
        else:
            # Modo de visualização
            st.text_area(
                "Observações:",
                value=st.session_state.observacoes.get(unique_id, ""),
                key=f"obs_view_{unique_id}",
                height=200,
                disabled=True
            )
            if st.button("✏️ Editar", key=f"edit_{unique_id}"):
                st.session_state.edit_mode[unique_id] = True
                st.rerun()
        
        # Botões na sidebar para geração de relatórios
        with st.sidebar:
            st.header("Gerar Relatórios")
            
            # Botão para gerar PDF individual
            if st.button("📄 Gerar Relatório Individual"):
                record_for_pdf = selected_record.copy()
                record_for_pdf['Observações'] = st.session_state.observacoes.get(unique_id, "")
                
                # Obtém a imagem do session_state, se existir
                image_data = st.session_state.imagens.get(unique_id)
                
                try:
                    pdf = create_pdf(record_for_pdf, image_data)
                    
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                        pdf.output(tmp.name)
                        tmp.seek(0)
                        pdf_bytes = tmp.read()
                    
                    b64 = base64.b64encode(pdf_bytes).decode()
                    href = f'<a href="data:application/pdf;base64,{b64}" download="relatorio_{selected_record["Processo"]}.pdf">⬇️ Baixar Relatório Individual</a>'
                    st.markdown(href, unsafe_allow_html=True)
                    st.success("Relatório individual gerado!")
                except Exception as e:
                    st.error(f"Erro ao gerar PDF: {e}")
            
            # Botão para gerar relatório completo
            if st.button("📚 Gerar Relatório Completo"):
                records_for_pdf = []
                
                for _, row in df.iterrows():
                    record = row.to_dict()
                    record['Observações'] = st.session_state.observacoes.get(row['unique_id'], "")
                    records_for_pdf.append(record)
                
                try:
                    pdf = create_full_pdf(records_for_pdf)
                    
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                        pdf.output(tmp.name)
                        tmp.seek(0)
                        pdf_bytes = tmp.read()
                    
                    b64 = base64.b64encode(pdf_bytes).decode()
                    href = f'<a href="data:application/pdf;base64,{b64}" download="relatorio_completo.pdf">⬇️ Baixar Relatório Completo</a>'
                    st.markdown(href, unsafe_allow_html=True)
                    st.success(f"Relatório completo com {len(records_for_pdf)} processos gerado!")
                except Exception as e:
                    st.error(f"Erro ao gerar PDF completo: {e}")
            
            # Botão para exportar dados atualizados
            st.header("Exportar Dados")
            if st.button("💾 Exportar Excel Atualizado"):
                # Atualizar todas as observações no DataFrame antes de exportar
                for uid, obs in st.session_state.observacoes.items():
                    df.loc[df['unique_id'] == uid, obs_col] = obs
                
                # Criar arquivo Excel em memória
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False)
                output.seek(0)
                
                # Criar link para download
                b64 = base64.b64encode(output.read()).decode()
                href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="mandados_atualizados.xlsx">⬇️ Baixar Excel Atualizado</a>'
                st.markdown(href, unsafe_allow_html=True)
                st.success("Dados exportados com sucesso!")
        
    else:
        st.error("Não foi possível carregar os dados do arquivo.")
else:
    st.info("Por favor, carregue um arquivo Excel para começar.")