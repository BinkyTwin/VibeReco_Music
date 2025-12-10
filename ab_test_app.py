import streamlit as st
import pandas as pd
from src.pipeline import MusicPipeline
from src.ab_testing import ABTestManager

# --- CONFIGURATION ---
st.set_page_config(
    page_title="VibeReco vs YouTube - A/B Testing Studio",
    layout="wide"
)

# --- STYLES ---
st.markdown("""
<style>
    .song-card {
        padding: 8px 10px;
        border-radius: 4px;
        margin-bottom: 6px;
        background-color: #f5f5f7;
        border: 1px solid #e0e0e0;
        font-size: 0.9rem;
    }
    .section-box {
        padding: 16px 18px;
        border-radius: 6px;
        border: 1px solid #e0e0e0;
        background-color: #fafafa;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

def main():
    st.title("VibeReco vs YouTube – Blind A/B Testing")

    ab_manager = ABTestManager()

    if "test_data" not in st.session_state:
        st.session_state.test_data = None
    if "test_completed" not in st.session_state:
        st.session_state.test_completed = False

    tab_test, tab_stats = st.tabs(["Blind test", "Statistiques"])

    # --- TAB 1: RUN TEST ---
    with tab_test:
        # Zone de configuration en haut, au centre
        config_col, info_col = st.columns([1, 1.4])

        with config_col:
            st.markdown("### Configuration du test")
            query = st.text_input(
                "Morceau de départ (Titre - Artiste)",
                placeholder="Ex. Dreams - Fleetwood Mac"
            )
            limit = st.slider("Nombre de titres à comparer", 5, 30, 15, 1)

            generate = st.button("Générer le blind test")

            if generate:
                if not query:
                    st.error("Merci de saisir un morceau de départ.")
                else:
                    with st.spinner("Génération des playlists YouTube et VibeReco..."):
                        pipeline = MusicPipeline()
                        results = pipeline.run(query, limit=limit, return_youtube_tracks=True)

                        if results and results.get("final_tracks"):
                            yt_tracks = results["youtube_tracks"]
                            vibe_tracks = results["final_tracks"]

                            blind_setup = ab_manager.prepare_blind_test(yt_tracks, vibe_tracks)
                            st.session_state.test_data = blind_setup
                            st.session_state.test_completed = False
                            st.session_state.seed_query = query
                        else:
                            st.error("Impossible de générer des recommandations. Essaie avec un autre morceau.")

        with info_col:
            st.markdown("### Comment fonctionne ce test")
            st.markdown(
                """
                Ce module affiche deux playlists anonymisées construites à partir du même morceau de départ.  
                L'une est générée par YouTube, l'autre par VibeReco, mais tu ne sais pas laquelle est laquelle.  

                Tu compares uniquement la cohérence de la vibe, puis tu votes et notes la qualité perçue.  
                Les résultats sont agrégés dans l'onglet Statistiques.
                """
            )

        st.markdown("---")

        # Zone principale du test
        if st.session_state.test_data and not st.session_state.test_completed:
            data = st.session_state.test_data

            st.subheader(f"Blind test pour : {st.session_state.seed_query}")
            st.caption("Compare les deux playlists uniquement sur la vibe et la continuité ressentie.")

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("#### Playlist A")
                box_a = st.container()
                with box_a:
                    for i, track in enumerate(data["A"]):
                        st.markdown(
                            f"<div class='song-card'><strong>{i+1}. {track['title']}</strong><br>"
                            f"{track['artist']}</div>",
                            unsafe_allow_html=True
                        )

            with col2:
                st.markdown("#### Playlist B")
                box_b = st.container()
                with box_b:
                    for i, track in enumerate(data["B"]):
                        st.markdown(
                            f"<div class='song-card'><strong>{i+1}. {track['title']}</strong><br>"
                            f"{track['artist']}</div>",
                            unsafe_allow_html=True
                        )

            st.markdown("---")

            st.markdown("### Évaluation")

            with st.form("voting_form"):
                left, right = st.columns(2)

                with left:
                    choice = st.radio(
                        "Quelle playlist a la meilleure vibe globale",
                        ["Playlist A", "Playlist B"],
                        horizontal=True
                    )

                with right:
                    st.caption("Notes de 1 (faible) à 5 (forte).")

                c1, c2, c3 = st.columns(3)
                with c1:
                    score_emo = st.slider("Cohérence émotionnelle", 1, 5, 3)
                with c2:
                    score_narrative = st.slider("Cohérence narrative/thématique", 1, 5, 3)
                with c3:
                    score_keep = st.slider("Envie de garder la playlist", 1, 5, 3)

                submit_vote = st.form_submit_button("Enregistrer le vote")

                if submit_vote:
                    vote_key = "A" if choice == "Playlist A" else "B"
                    scores = {
                        "emotional": score_emo,
                        "narrative": score_narrative,
                        "keepability": score_keep
                    }

                    ab_manager.save_vote(data, vote_key, scores, st.session_state.seed_query)
                    st.session_state.test_completed = True
                    st.session_state.last_winner = data["mapping"][vote_key]
                    st.rerun()

        elif st.session_state.test_completed:
            winner = st.session_state.last_winner
            winner_pretty = "VibeReco" if winner == "vibe" else "YouTube"

            st.success(f"Vote enregistré. Playlist préférée : {winner_pretty}")

            if winner == "vibe":
                st.markdown(
                    "Pour ce test, VibeReco a mieux aligné la playlist sur la vibe perçue à partir du morceau de départ."
                )

            if st.button("Lancer un nouveau test"):
                st.session_state.test_data = None
                st.session_state.test_completed = False
                st.rerun()

    # --- TAB 2: STATS ---
    with tab_stats:
        st.header("Statistiques globales")
        stats = ab_manager.get_stats()

        if stats:
            col_a, col_b, col_c = st.columns(3)
            col_a.metric("Nombre de votes", stats["total_votes"])
            col_b.metric("Victoires VibeReco", stats["vibe_wins"])
            col_c.metric("Victoires YouTube", stats["youtube_wins"])

            st.markdown("---")

            win_rate = stats["vibe_win_rate"]
            st.subheader(f"Taux de victoire de VibeReco : {win_rate:.1f}%")
            st.progress(win_rate / 100)

            if win_rate > 50:
                st.success("Pour l'instant, VibeReco surpasse la baseline.")
            else:
                st.warning("Pour l'instant, YouTube reste meilleur. Il faudra peut-être ajuster l'algorithme.")
        else:
            st.info("Pas encore de données. Lance quelques tests pour commencer.")

if __name__ == "__main__":
    main()
