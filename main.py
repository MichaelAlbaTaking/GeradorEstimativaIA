import streamlit as st
import yaml
import json
import httpx
import openai
import PyPDF2
import io
import math
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import mm
from PIL import Image

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Estimador de Projetos IA", layout="wide")

# --- TEMPLATE YAML PADRÃO ---
DEFAULT_CONFIG = """
equipe:
  - cargo: "Arquiteto de Software"
    senioridade: "Senior"
    quantidade: 1
    custo_hora: 250
  - cargo: "Desenvolvedor Fullstack"
    senioridade: "Pleno"
    quantidade: 2
    custo_hora: 150
  - cargo: "QA / Tester"
    senioridade: "Pleno"
    quantidade: 1
    custo_hora: 100
  - cargo: "Gerente de Projetos"
    senioridade: "Senior"
    quantidade: 1
    custo_hora: 200

regras_negocio:
  margem_risco_percentual: 0.20
  regras_condicionais:
    - se: "Integração com legado"
      adicionar_horas: 40
    - se: "Documentação técnica escassa"
      adicionar_horas: 20
  complexidade:
    baixa: 1.0
    media: 1.5
    alta: 2.0
  multiplicadores_tecnicos:
    sem_stack_definida: 1.3
    sem_infra_definida: 1.2
  tabela_esforco_base:
    tela_simples_informativa: 8
    tela_complexa_dashboard: 16
    autenticacao_seguranca: 12
    integracao_banco_api: 24
    exportacao_relatorio_pdf: 8
  distribuicao_esforco:
    "Arquiteto de Software": 0.15
    "Desenvolvedor Fullstack": 0.55
    "QA / Tester": 0.20
    "Gerente de Projetos": 0.10
"""

if 'yaml_config' not in st.session_state:
    st.session_state.yaml_config = DEFAULT_CONFIG
if 'estimativa_resultado' not in st.session_state:
    st.session_state.estimativa_resultado = None

# --- FUNÇÕES ---
def extract_text_from_file(uploaded_file):
    text = ""
    try:
        if uploaded_file.type == "application/pdf":
            pdf_reader = PyPDF2.PdfReader(uploaded_file)
            for page in pdf_reader.pages:
                text += page.extract_text() or ""
        elif uploaded_file.type == "text/plain":
            text = uploaded_file.read().decode("utf-8")
    except Exception as e:
        st.error(f"Erro ao extrair texto: {e}")
    return text

def call_openrouter(api_key, prompt, yaml_config_str):
    client = openai.OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
        http_client=httpx.Client(),
    )
    
    config = yaml.safe_load(yaml_config_str)
    cargos = [e['cargo'] for e in config['equipe']]
    
    system_prompt = f"""Você é um Arquiteto de Software Sênior. Sua missão é gerar uma estimativa técnica infalível.

    DIRETRIZES TÉCNICAS (YAML):
    {yaml_config_str}

    FLUXO DE CÁLCULO OBRIGATÓRIO:
    1. Liste todas as atividades/passos identificados no documento.
    2. Use EXCLUSIVAMENTE os valores da 'tabela_esforco_base'.
    3. Atribua cada atividade ao perfil correto: {cargos}.
    4. Aplique multiplicadores técnicos sobre as horas de cada tarefa se necessário.

    ESTRUTURA OBRIGATÓRIA DO JSON DE SAÍDA:
    {{
      "resumo_entendimento": "Resumo do que foi compreendido",
      "memoria_calculo_e_gaps": "Explique a matemática dos multiplicadores aplicados e as restrições técnicas",
      "atividades_detalhadas": [
         {{"perfil": "Nome Exato do Cargo", "atividade": "Descrição da atividade", "horas": 0}}
      ],
      "cronograma_semanas": [
         {{"periodo": "Semana 1", "foco": "Foco principal da semana", "responsaveis": "Perfis responsáveis"}}
      ],
      "perguntas_clarificacao": ["Pergunta 1", "Pergunta 2"],
      "riscos_identificados": ["Risco 1", "Risco 2"]
    }}
    """

    response = client.chat.completions.create(
        model="openai/gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Estime este escopo: {prompt}"}
        ],
        response_format={"type": "json_object"},
        temperature=0
    )
    
    try:
        data = json.loads(response.choices[0].message.content)
        
        # --- RE-CÁLCULO MATEMÁTICO NO PYTHON PARA BLINDAGEM ---
        custos_map = {e['cargo']: e['custo_hora'] for e in config['equipe']}
        margem_pct = config['regras_negocio'].get('margem_risco_percentual', 0)
        
        # Consolida investimento por perfil
        invest_perfil = {}
        for cargo in cargos:
            invest_perfil[cargo] = {"perfil": cargo, "horas_base": 0, "horas_extras": 0, "total_horas": 0, "custo_total": 0}
        
        # Processa atividades detalhadas
        for ativ in data.get("atividades_detalhadas", []):
            perfil = ativ.get("perfil")
            if perfil in invest_perfil:
                h = math.ceil(float(ativ.get("horas", 0)))
                ativ["horas"] = h # Atualiza para o arredondado
                invest_perfil[perfil]["horas_base"] += h
        
        subtotal = 0
        for cargo, info in invest_perfil.items():
            info["total_horas"] = info["horas_base"] + info["horas_extras"] # Horas extras não são geradas pela IA neste fluxo, mas mantidas para compatibilidade
            info["custo_total"] = info["total_horas"] * custos_map.get(cargo, 0)
            subtotal += info["custo_total"]
            
        data["investimento_por_perfil"] = [v for v in invest_perfil.values() if v["total_horas"] > 0]
        data["totais_financeiros"] = {
            "subtotal": subtotal,
            "margem_risco_valor": subtotal * margem_pct,
            "total_geral": subtotal + (subtotal * margem_pct)
        }
            
        # Fallbacks para chaves de texto e listas que a IA pode esquecer
        data.setdefault("resumo_entendimento", "Resumo não disponível.")
        data.setdefault("memoria_calculo_e_gaps", "Memória de cálculo e análise de gaps não disponível.")
        data.setdefault("atividades_detalhadas", [])
        data.setdefault("cronograma_semanas", [])
        data.setdefault("perguntas_clarificacao", [])
        data.setdefault("riscos_identificados", [])
            
        return data
    except Exception as e:
        st.error(f"Erro na blindagem dos dados: {e}")
        return None

def generate_pdf(data, metadata, logo=None):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=15*mm, leftMargin=15*mm, topMargin=15*mm, bottomMargin=15*mm)
    styles = getSampleStyleSheet()
    content_style = ParagraphStyle('ContentStyle', parent=styles['Normal'], fontSize=10, leading=14, spaceAfter=8)
    table_cell_style = ParagraphStyle('TableCellStyle', parent=styles['Normal'], fontSize=8, leading=10)
    
    elements = []
    if logo:
        try:
            img = Image.open(logo)
            img_buffer = io.BytesIO()
            img.save(img_buffer, format="PNG")
            img_buffer.seek(0)
            elements.append(RLImage(img_buffer, width=40*mm, height=20*mm))
            elements.append(Spacer(1, 10*mm))
        except: pass

    elements.append(Paragraph(f"PROPOSTA TÉCNICA: {metadata.get('projeto')}", styles['Title']))
    elements.append(Paragraph(f"Cliente: {metadata.get('cliente')}", styles['Heading2']))
    
    # 1. Resumo e Memória
    elements.append(Paragraph("1. Resumo do Entendimento", styles['Heading3']))
    elements.append(Paragraph(str(data.get('resumo_entendimento', '')), content_style))
    
    elements.append(Paragraph("2. Memória de Cálculo e Gaps", styles['Heading3']))
    memoria_txt = str(data.get('memoria_calculo_e_gaps', '')).replace('\n', '<br/>')
    elements.append(Paragraph(memoria_txt, content_style))

    # 3. Atividades Detalhadas
    elements.append(Paragraph("3. Detalhamento de Atividades", styles['Heading3']))
    ativ_data = [["Perfil", "Atividade", "Horas"]]
    for a in data.get('atividades_detalhadas', []):
        ativ_data.append([Paragraph(a.get('perfil', ''), table_cell_style), Paragraph(a.get('atividade', ''), table_cell_style), str(a.get('horas', 0))])
    
    at = Table(ativ_data, colWidths=[40*mm, 115*mm, 20*mm])
    at.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#444444")), ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke), ('GRID', (0, 0), (-1, -1), 0.5, colors.grey), ('VALIGN', (0, 0), (-1, -1), 'TOP')]))
    elements.append(at)
    elements.append(Spacer(1, 8*mm))

    # 4. Investimento
    elements.append(Paragraph("4. Investimento por Perfil", styles['Heading3']))
    inv_data = [["Perfil", "H. Base", "H. Extras", "Total", "Custo Total"]]
    for i in data.get('investimento_por_perfil', []):
        inv_data.append([i.get('perfil'), str(i.get('horas_base')), str(i.get('horas_extras')), str(i.get('total_horas')), f"R$ {i.get('custo_total'):,.2f}"])
    
    totais = data.get('totais_financeiros', {})
    inv_data.append(["SUBTOTAL", "", "", "", f"R$ {totais.get('subtotal', 0):,.2f}"])
    inv_data.append(["RISCO", "", "", "", f"R$ {totais.get('margem_risco_valor', 0):,.2f}"])
    inv_data.append(["TOTAL GERAL", "", "", "", f"R$ {totais.get('total_geral', 0):,.2f}"])
    
    it = Table(inv_data, colWidths=[55*mm, 20*mm, 20*mm, 20*mm, 60*mm])
    it.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1F4E79")), ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke), ('GRID', (0, 0), (-1, -1), 0.5, colors.grey), ('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey), ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold')]))
    elements.append(it)
    
    # 5. Cronograma
    elements.append(Spacer(1, 10*mm))
    elements.append(Paragraph("5. Cronograma por Semanas", styles['Heading3']))
    cron_data = [["Período", "Foco", "Responsáveis"]]
    for s in data.get('cronograma_semanas', []):
        cron_data.append([Paragraph(s.get('periodo', ''), table_cell_style), Paragraph(s.get('foco', ''), table_cell_style), Paragraph(s.get('responsaveis', ''), table_cell_style)])
    
    st_table = Table(cron_data, colWidths=[30*mm, 90*mm, 55*mm])
    st_table.setStyle(TableStyle([('GRID', (0, 0), (-1, -1), 0.5, colors.grey), ('VALIGN', (0, 0), (-1, -1), 'TOP'), ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey)]))
    elements.append(st_table)

    # 6. Perguntas de Clarificação
    elements.append(Spacer(1, 10*mm))
    elements.append(Paragraph("6. Perguntas de Clarificação", styles['Heading3']))
    if data.get('perguntas_clarificacao'):
        for i, p in enumerate(data['perguntas_clarificacao']):
            elements.append(Paragraph(f"• {p}", content_style))
    else:
        elements.append(Paragraph("Nenhuma pergunta de clarificação identificada.", content_style))

    # 7. Riscos Identificados
    elements.append(Spacer(1, 10*mm))
    elements.append(Paragraph("7. Riscos Potenciais", styles['Heading3']))
    if data.get('riscos_identificados'):
        for i, r in enumerate(data['riscos_identificados']):
            elements.append(Paragraph(f"• {r}", content_style))
    else:
        elements.append(Paragraph("Nenhum risco significativo identificado.", content_style))


    doc.build(elements)
    buffer.seek(0)
    return buffer

# --- UI ---
with st.sidebar:
    st.header("⚙️ Configurações")
    api_key = st.text_input("OpenRouter API Key", type="password")
    logo_file = st.file_uploader("Logo", type=["png", "jpg"])
    yaml_input = st.text_area("Template YAML", value=st.session_state.yaml_config, height=350)
    st.session_state.yaml_config = yaml_input

st.title("🚀 Estimador de Projetos IA")
c1, c2 = st.columns([1, 1.2])

with c1:
    cliente = st.text_input("Cliente")
    projeto = st.text_input("Projeto")
    arquivo = st.file_uploader("Documento de Escopo", type=["pdf", "txt"])
    if st.button("Gerar Proposta Completa ✨", type="primary"):
        if not api_key or not arquivo: st.error("Faltam dados!")
        else:
            with st.spinner("Analisando e calculando proposta..."):
                texto = extract_text_from_file(arquivo)
                res = call_openrouter(api_key, texto, st.session_state.yaml_config)
                if res: st.session_state.estimativa_resultado = res

with c2:
    if st.session_state.estimativa_resultado:
        res = st.session_state.estimativa_resultado
        tab1, tab2, tab3, tab4 = st.tabs(["💰 Proposta", "📝 Atividades", "📅 Cronograma", "❓ Gaps & Riscos"])
        
        with tab1:
            tot = res.get('totais_financeiros', {})
            st.metric("Total Geral", f"R$ {tot.get('total_geral', 0):,.2f}")
            st.write("### Investimento por Perfil")
            st.table(res.get('investimento_por_perfil', []))
            
            pdf = generate_pdf(res, {"cliente": cliente, "projeto": projeto}, logo_file)
            st.download_button("📄 Baixar PDF Completo", data=pdf, file_name=f"Proposta_{cliente}.pdf", use_container_width=True)

        with tab2:
            st.write("### Decomposição de Atividades")
            st.table(res.get('atividades_detalhadas', []))
            st.write("#### Memória de Cálculo")
            st.info(res.get('memoria_calculo_e_gaps'))

        with tab3:
            st.write("### Cronograma por Semanas")
            st.table(res.get('cronograma_semanas', []))
            
        with tab4:
            st.write("#### Perguntas de Clarificação")
            for p in res.get('perguntas_clarificacao', []): st.write(f"- {p}")
            st.write("#### Riscos Identificados")
            for r in res.get('riscos_identificados', []): st.warning(r)
    else: st.info("Aguardando escopo...")
