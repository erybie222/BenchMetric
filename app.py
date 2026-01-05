import time

import streamlit as st
import tempfile
from main import analyze

def app():
    imgW, imgH = 1280, 720


    st.set_page_config(page_title="AI Coach", layout="wide")

    with st.container(horizontal_alignment="center"):
        st.title("Bench press analyzer - AI Coach")
        st.markdown("---")

        uploaded_file = st.file_uploader("Upload your bench press video", type=['mp4'])

        if uploaded_file is not None:
            tfile = tempfile.NamedTemporaryFile(delete=False)
            tfile.write(uploaded_file.read())
            tfile.close()

            delay = st.slider("Delay", min_value=0.0, max_value=1.0, value=0.1)
            isRight = st.toggle('Right mode', value=False)

            if isRight:
                side = 'right'
            else:
                side = 'left'

            if st.button("Analyze video"):

                progress_text = "Video analyze in progress. Please wait."
                my_bar = st.progress(0, text=progress_text)

                st.write("Analyzing your video in progress...")
                st.markdown("---")
                metrics = analyze(tfile.name, imgW, imgH, True, delay, side, progress_bar=my_bar)

                my_bar.progress(100, text="Analysis complete!")
                time.sleep(0.5)
                my_bar.empty()

                if len(metrics) > 0:
                    st.markdown("---")
                    st.header("📊 Technique analysis")
                    st.write("Metrics:")
                    st.dataframe(metrics)
                    plotVelocity(metrics)
                    plotDuration(metrics)
                    plotPhaseDuration(metrics)
                    plotRepDistacne(metrics)



def plotVelocity(metrics):
    st.subheader("Velocity chart")
    df_filtered = metrics[metrics["Phase"] == "CONCENTRIC"]
    df_rep_velocity = df_filtered.set_index("Repetition")["Velocity_avg"]

    st.line_chart(data=df_rep_velocity, x_label='Repetition', y_label='Average velocity in concentric phase [px/s]' )

    c1, c2 = st.columns(2)
    avg_vel = df_rep_velocity.mean(axis=0)
    max_vel = df_rep_velocity.max(axis=0)
    with c1:
        st.markdown(f"<p style='text-align: center;'>Average velocity: {avg_vel:.2f} [px/s]</p>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<p style='text-align: center;'>Max velocity: {max_vel:.2f} [px/s]</p>", unsafe_allow_html=True)

def plotDuration(metrics):
    st.subheader("Repetition duration chart")
    df_filtered = metrics.set_index("Repetition")["Duration_s"]
    df_rep_duration = df_filtered.groupby("Repetition").sum()
    st.line_chart(df_rep_duration, x_label="Repetition", y_label="Duration [s]")

    c1, c2, c3 = st.columns(3)
    min_dur = df_rep_duration.min(axis=0)
    avg_dur = df_rep_duration.mean(axis=0)
    max_dur = df_rep_duration.max(axis=0)
    with c1:
        st.markdown(f"<p style='text-align: center;'>Min duration: {min_dur:.2f} [s]</p>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<p style='text-align: center;'>Average duration: {avg_dur:.2f} [s]</p>", unsafe_allow_html=True)
    with c3:
        st.markdown(f"<p style='text-align: center;'>Max duration: {max_dur:.2f} [s]</p>", unsafe_allow_html=True)


def plotPhaseDuration(metrics):
    st.subheader("Phase duration chart")

    df_pivot = metrics.pivot_table(index="Repetition", columns="Phase", values="Duration_s")

    columns = df_pivot.columns
    colors = []
    if "START" in columns: colors.append("#0000FF")
    if "ECCENTRIC" in columns: colors.append("#FF00FF")
    if "BOTTOM" in columns:    colors.append("#FF0000")
    if "CONCENTRIC" in columns: colors.append("#00FF00")

    if not colors:
        colors = None

    st.bar_chart(
        df_pivot,
        x_label="Repetition",
        y_label="Phase Duration [s]",
        color=colors,
        stack=False
    )

def plotRepDistance(metrics):
    st.subheader("Rep distance chart")
    df_indexed = metrics.set_index("Repetition")["Distance_px"]
    df_distance_rep = df_indexed.groupby("Repetition").sum()
    st.bar_chart(df_distance_rep, x_label="Repetition", y_label="Barbell distance [px]",)

if __name__ == '__main__':
    app()