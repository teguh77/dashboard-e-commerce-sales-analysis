import altair as alt
import folium
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
from babel.numbers import format_currency
from folium import CircleMarker
from streamlit_folium import st_folium

st.set_page_config(
    page_title="E-commerce Dashboard",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# Load data
main_df = pd.read_csv("main_data.csv")


# Global variables
orders_per_hour = main_df.groupby("order_hour")["order_id"].count()
orders_per_hour.index = orders_per_hour.index.map(
    lambda x: f"{x % 12 or 12} {'AM' if x < 12 else 'PM'}"
)
hourly_orders_df = orders_per_hour.sort_values(ascending=False).reset_index()

orders_per_day_df = (
    main_df.groupby("order_day")["order_id"]
    .count()
    .sort_values(ascending=False)
    .reset_index()
)
orders_per_month_df = (
    main_df.groupby("order_month")["order_id"]
    .count()
    .sort_values(ascending=False)
    .reset_index()
)


# Helper functions
def create_margin_total(df):
    return format_currency(df["profit_margin"].sum(), "BRL", locale="pt_BR")


def create_best_product_category(df):
    return (
        df.groupby("product_category_name_english")["product_id"]
        .nunique()
        .idxmax()
        .replace("_", " ")
        .title()
    )


def create_delivery_time_average(df):
    return f"{round(df['delivery_time'].mean())} days"


def create_review_score_average(df):
    return f"{df['review_score'].mean():.2f}"


def create_category_base_on_profit(df):
    category = (
        df.groupby(by="product_category_name_english")
        .agg({"profit_margin": "sum"})
        .reset_index()
        .sort_values(by="profit_margin")
    )

    category["product_category_name_english"] = (
        category["product_category_name_english"].str.replace("_", " ").str.title()
    )

    return category


def create_correlation_score(df):
    return f"{df["delivery_time"].corr(df["review_score"]):.2f}"


def create_need_attention_city(df):
    return df[
        (df["delivery_time_category"] == "Lambat")
        & (df["review_score_category"] == "Kurang Baik")
    ][
        [
            "geolocation_city",
            "geolocation_lat",
            "geolocation_lng",
            "review_score",
            "customer_state",
        ]
    ].drop_duplicates(
        subset=["geolocation_city"]
    )


def create_top_selling_product_category(df):
    category = (
        df.groupby(by="product_category_name_english")["product_id"]
        .nunique()
        .reset_index()
        .sort_values(by="product_id", ascending=False)
        .head(5)
    )

    category["product_category_name_english"] = (
        category["product_category_name_english"].str.replace("_", " ").str.title()
    )

    return category


def create_top_selling_product_city(df):
    category = (
        df.groupby(by="geolocation_city")["product_id"]
        .nunique()
        .reset_index()
        .sort_values(by="product_id", ascending=False)
        .head(5)
    )

    category["geolocation_city"] = (
        category["geolocation_city"].str.replace("_", " ").str.title()
    )

    return category


margin_total_df = create_margin_total(main_df)
best_product_category_df = create_best_product_category(main_df)
delivery_time_average_df = create_delivery_time_average(main_df)
review_score_average_df = create_review_score_average(main_df)
category_base_on_profit_df = create_category_base_on_profit(main_df)
need_attention_city_df = create_need_attention_city(main_df)
correlation_score_df = create_correlation_score(main_df)
top_selling_product_category_df = create_top_selling_product_category(main_df)
top_selling_product_city_df = create_top_selling_product_city(main_df)


# Streamlit app
st.header("Dashboard E-Commerce Sales Analysis")
st.markdown("<div style='margin-bottom: 2rem;'></div>", unsafe_allow_html=True)

metric1, metric2, metric3, metric4 = st.columns(4, gap="medium")

with metric1:
    st.metric(label="Margin Total", value=margin_total_df)
with metric2:
    st.metric(label="Best Product Category", value=best_product_category_df)
with metric3:
    st.metric(label="Delivery Time Average", value=delivery_time_average_df)
with metric4:
    st.metric(label="Review Score Average", value=review_score_average_df)

st.markdown("<div style='margin-bottom: 4rem;'></div>", unsafe_allow_html=True)

st.subheader("Top and Bottom Product Categories by Profit Margin")
profit1, profit2 = st.columns(2, gap="large")
with profit1:
    st.markdown(
        "<p style='font-size: 18px; display: flex; align-items: center; justify-content: center;'>Top 5 Product Categories with Highest Profit Margin</p>",
        unsafe_allow_html=True,
    )
    base = alt.Chart(
        category_base_on_profit_df.nlargest(5, "profit_margin"), height=400
    ).encode(
        x=alt.X("profit_margin:Q", title="Profit Margin (BRL)"),
        y=alt.Y("product_category_name_english:O", title="Product Category").sort("-x"),
        text=alt.Text("profit_margin:Q", format=",.0f"),
        tooltip=[
            alt.Tooltip("product_category_name_english:N", title="Product Category"),
            alt.Tooltip("profit_margin:Q", title="Profit Margin", format=",.0f"),
        ],
    )

    bars = base.mark_bar().encode(
        color=alt.Color(
            "profit_margin:Q", scale=alt.Scale(scheme="greens"), legend=None
        ),
    )

    text = base.mark_text(
        align="right",
        dx=-10,
        color=alt.expr(
            "luminance(scale('color', datum.profit_margin)) > 0.5 ? 'black' : 'white'"
        ),
    )
    final_chart = bars + text

    st.altair_chart(final_chart, use_container_width=True)
with profit2:
    st.markdown(
        "<p style='font-size: 18px;display: flex; align-items: center; justify-content: center;'>Top 5 Product Categories with Lowest Profit Margin</p>",
        unsafe_allow_html=True,
    )
    base = alt.Chart(
        category_base_on_profit_df.nsmallest(5, "profit_margin"), height=400
    ).encode(
        x=alt.X("profit_margin:Q", title="Profit Margin (BRL)"),
        y=alt.Y("product_category_name_english:O", title="Product Category").sort("-x"),
        text=alt.Text("profit_margin:Q", format=",.0f"),
        tooltip=[
            alt.Tooltip("product_category_name_english:N", title="Product Category"),
            alt.Tooltip("profit_margin:Q", title="Profit Margin", format=",.0f"),
        ],
    )

    bars = base.mark_bar().encode(
        color=alt.Color("profit_margin:Q", scale=alt.Scale(scheme="reds"), legend=None),
    )

    text = base.mark_text(
        align="right",
        dx=-10,
        color=alt.expr(
            "luminance(scale('color', datum.profit_margin)) > 0.5 ? 'black' : 'white'"
        ),
    )
    final_chart = bars + text

    st.altair_chart(final_chart, use_container_width=True)

st.markdown("<div style='margin-bottom: 4rem;'></div>", unsafe_allow_html=True)

st.subheader("Best Time for Promotions Based on Customer Order Activity")
order1, order2, order3 = st.columns(3, gap="medium")

with order1:
    st.markdown(
        "<p style='font-size: 18px;display: flex; align-items: center; justify-content: center;'>Busiest Hours for Customer Orders</p>",
        unsafe_allow_html=True,
    )
    base = alt.Chart(hourly_orders_df).encode(
        x=alt.X("order_hour", title="Time"),
        y=alt.Y("order_id", title="Order Count"),
        text=alt.Text("order_id:Q", format=",.0f"),
        tooltip=[
            alt.Tooltip("order_hour:N", title="Time"),
            alt.Tooltip("order_id:Q", title="Order Count", format=",.0f"),
        ],
    )

    lines = base.mark_line(interpolate="natural", color="aqua")

    points = base.mark_point(filled=True).encode(
        color=alt.Color(
            "order_hour:N", scale=alt.Scale(scheme="bluepurple"), legend=None
        ),
    )

    text = base.mark_text(
        align="left",
        dx=5,
        dy=-5,
        color="white",
        fontSize=10,
        fontWeight="bold",
    )
    chart = lines + points + text

    st.altair_chart(chart, use_container_width=True)
with order2:
    st.markdown(
        "<p style='font-size: 18px;display: flex; align-items: center; justify-content: center;'>Busiest Days for Customer Orders</p>",
        unsafe_allow_html=True,
    )
    base = alt.Chart(orders_per_day_df).encode(
        x=alt.X("order_day:N", title="Day"),
        y=alt.Y("order_id:Q", title="Order Count"),
        text=alt.Text("order_id:Q", format=",.0f"),
        tooltip=[
            alt.Tooltip("order_day:N", title="Day"),
            alt.Tooltip("order_id:Q", title="Order Count", format=",.0f"),
        ],
    )

    bars = base.mark_bar().encode(
        color=alt.Color("order_id:Q", scale=alt.Scale(scheme="greens"), legend=None),
    )

    text = base.mark_text(
        align="center",
        dy=-10,
        color=alt.expr(
            "luminance(scale('color', datum.order_id)) > 0.5 ? 'black' : 'white'"
        ),
    )
    final_chart = bars + text

    st.altair_chart(final_chart, use_container_width=True)
with order3:
    st.markdown(
        "<p style='font-size: 18px;display: flex; align-items: center; justify-content: center;'>Top Months for Customer Orders</p>",
        unsafe_allow_html=True,
    )
    base = alt.Chart(orders_per_month_df).encode(
        x=alt.X("order_month:N", title="Month"),
        y=alt.Y("order_id:Q", title="Order Count"),
        text=alt.Text("order_id:Q", format=",.0f"),
        tooltip=[
            alt.Tooltip("order_month:N", title="Month"),
            alt.Tooltip("order_id:Q", title="Order Count", format=",.0f"),
        ],
    )

    bars = base.mark_bar().encode(
        color=alt.Color("order_id:Q", scale=alt.Scale(scheme="greens"), legend=None),
    )

    text = base.mark_text(align="center", dy=-10, color="white")
    final_chart = bars + text

    st.altair_chart(final_chart, use_container_width=True)

st.markdown("<div style='margin-bottom: 4rem;'></div>", unsafe_allow_html=True)

st.subheader("Delivery Time and Review Correlation")
col = st.columns((0.8, 0.2), gap="medium")

with col[0]:
    scatter_regression = alt.Chart(main_df).mark_point(
        size=60, filled=True, color="aqua"
    ).encode(
        x=alt.X("delivery_time:Q", title="Delivery Time"),
        y=alt.Y("review_score:Q", title="Review Score"),
        tooltip=["delivery_time", "review_score"],
    ) + alt.Chart(
        main_df
    ).mark_line(
        color="red"
    ).transform_regression(
        "delivery_time", "review_score"
    ).encode(
        x="delivery_time:Q",
        y="review_score:Q",
    )
    st.altair_chart(scatter_regression, use_container_width=True)
with col[1]:
    st.metric(
        label="Delivery Time and Review Correlation Score",
        value=correlation_score_df,
    )


st.markdown("<div style='margin-bottom: 4rem;'></div>", unsafe_allow_html=True)

prod1, prod2 = st.columns(2, gap="large")


with prod1:
    st.markdown(
        "<p style='font-size: 18px;display: flex; align-items: center; justify-content: center;'>Priority Cities and Regions for Faster Delivery to Enhance Customer Reviews</p>",
        unsafe_allow_html=True,
    )

    attention_city_map = folium.Map(
        location=[-15.7801, -47.9292],
        zoom_start=4,
        tiles="CartoDB positron",
        scrollWheelZoom=False,
    )

    def get_color(score):
        if score <= 2:
            return "#d73027"
        elif score <= 4:
            return "#fee08b"
        else:
            return "#1a9850"

    for _, row in need_attention_city_df.iterrows():
        folium.CircleMarker(
            location=[row["geolocation_lat"], row["geolocation_lng"]],
            radius=row["review_score"] * 2,
            color=get_color(row["review_score"]),
            fill=True,
            fill_color=get_color(row["review_score"]),
            fill_opacity=0.7,
            popup=folium.Popup(
                f"<b>Kota:</b> {row['geolocation_city']}<br>"
                f"<b>State:</b> {row['customer_state']}<br>"
                f"<b>Review Score:</b> {row['review_score']}",
                max_width=250,
            ),
        ).add_to(attention_city_map)

    st_folium(
        attention_city_map,
        returned_objects=[],
        width="100%",
    )


with prod2:
    row1 = st.container()
    row2 = st.container()
    with row1:
        st.markdown(
            "<p style='font-size: 18px;display: flex; align-items: center; justify-content: center;'>Top 5 Selling Product Categories</p>",
            unsafe_allow_html=True,
        )
        base1 = alt.Chart(top_selling_product_category_df).encode(
            x=alt.X("product_category_name_english:N", title="Product Category"),
            y=alt.Y("product_id:Q", title="Product Count"),
            text=alt.Text("product_id:Q", format=",.0f"),
            tooltip=[
                alt.Tooltip(
                    "product_category_name_english:N", title="Product Category"
                ),
                alt.Tooltip("product_id:Q", title="Product Count", format=",.0f"),
            ],
        )

        bars1 = base1.mark_bar().encode(
            color=alt.Color(
                "product_id:Q", scale=alt.Scale(scheme="viridis"), legend=None
            ),
        )

        text1 = base1.mark_text(align="center", dy=-10, color="white")
        final_chart1 = bars1 + text1

        st.altair_chart(final_chart1, use_container_width=True)
    with row2:
        st.markdown(
            "<p style='font-size: 18px;display: flex; align-items: center; justify-content: center;'>Top 5 Selling Product Cities</p>",
            unsafe_allow_html=True,
        )
        base2 = alt.Chart(top_selling_product_city_df).encode(
            x=alt.X("geolocation_city:N", title="City"),
            y=alt.Y("product_id:Q", title="Product Count"),
            text=alt.Text("product_id:Q", format=",.0f"),
            tooltip=[
                alt.Tooltip("geolocation_city:N", title="City"),
                alt.Tooltip("product_id:Q", title="Product Count", format=",.0f"),
            ],
        )

        bars2 = base2.mark_bar().encode(
            color=alt.Color(
                "product_id:Q", scale=alt.Scale(scheme="viridis"), legend=None
            ),
        )

        text2 = base2.mark_text(align="center", dy=-10, color="white")
        final_chart2 = bars2 + text2

        st.altair_chart(final_chart2, use_container_width=True)
