with col_dash:
    st.markdown("### 📊 Painel Analítico & Consenso (Global)")
    
    col_btn1, col_btn2 = st.columns([1, 1])
    with col_btn1:
        if st.button("🔄 Atualizar Painel", use_container_width=True):
            st.rerun()

    df_votos = pd.DataFrame(estado_global["votos"])

    # 4 ABAS SEPARADAS E DEDICADAS
    tab_pareto, tab_mediacao, tab_historico_pareceres, tab_dados = st.tabs([
        "Análise de Pareto", 
        "🤖 Mediador IA", 
        "📜 Histórico de Pareceres", 
        "Histórico de Votos"
    ])

    # ABA 1: PARÉTO
    with tab_pareto:
        fig = gerar_grafico_pareto(df_votos)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
            st.info("💡 **Princípio de Pareto (80/20):** Foque a discussão nas objeções à esquerda para resolver a maioria dos conflitos do grupo.")
        else:
            st.image("https://images.unsplash.com/photo-1531403009284-440f080d1e12?q=80&w=800&auto=format&fit=crop", caption="Aguardando registros de voto para gerar o gráfico.", use_container_width=True)
            st.info("Cadastre os primeiros votos para gerar o Painel de Pareto.")

    # ABA 2: GERAR MEDIACAO
    with tab_mediacao:
        st.subheader("🤖 Gerar Novo Parecer de Mediação")
        st.write("Clique no botão abaixo para processar todos os votos registrados e criar uma proposta neutra baseada na Análise de Pareto.")
        
        if st.button("Gerar e Salvar Substitutivo Oficial", use_container_width=True):
            if df_votos.empty:
                st.warning("⚠ Registre pelo menos um voto antes de gerar o parecer.")
            else:
                with st.spinner("🤖 Analisando objeções e construindo proposta neutra..."):
                    novo_parecer = gerar_mediacao_ia(df_votos, pauta_atual)
                    data_hora = datetime.now().strftime("%d/%m/%Y %H:%M")
                    
                    # Salva o parecer na lista dedicada
                    estado_global["pareceres"].insert(0, {
                        "data": data_hora,
                        "qtd_votos": len(df_votos),
                        "texto": novo_parecer
                    })
                    st.success("✅ Novo parecer gerado com sucesso! Acesse a aba '📜 Histórico de Pareceres' para visualizá-lo.")
                    st.markdown("---")
                    st.markdown(novo_parecer)

    # ABA 3: HISTÓRICO DE PARECERES (EXCLUSIVA)
    with tab_historico_pareceres:
        st.subheader("📜 Histórico de Pareceres de Mediação")
        
        if estado_global["pareceres"]:
            st.write(f"Total de pareceres registrados: **{len(estado_global['pareceres'])}**")
            for idx, p in enumerate(estado_global["pareceres"]):
                numero_parecer = len(estado_global['pareceres']) - idx
                with st.expander(f"📌 Parecer #{numero_parecer} — Gerado em {p['data']} ({p['qtd_votos']} votos considerados)", expanded=(idx == 0)):
                    st.markdown(p["texto"])
        else:
            st.info("ℹ️ Nenhum parecer foi salvo até o momento. Gere um parecer na aba **🤖 Mediador IA** para salvá-lo aqui.")

    # ABA 4: HISTÓRICO DE VOTOS
    with tab_dados:
        st.subheader("📋 Registro Geral de Votos")
        st.dataframe(df_votos, use_container_width=True)
