import streamlit as st

# ----------------------------
#  Convert input time to microseconds
# ----------------------------
def to_microseconds(value, unit):
    if unit == "ns":
        return value / 1000
    if unit == "us":
        return value
    if unit == "ms":
        return value * 1000
    if unit == "s":
        return value * 1_000_000
    raise ValueError("Unit must be 'ns', 'us', 'ms', 's'")


# ----------------------------
#  Convert back from microseconds
# ----------------------------
def from_microseconds(value_us, unit):
    if unit == "ns":
        return value_us * 1000
    if unit == "us":
        return value_us
    if unit == "ms":
        return value_us / 1000
    if unit == "s":
        return value_us / 1_000_000


# ----------------------------
#  Compute all WDT intervals (with CS dividers)
# ----------------------------
def compute_wdt_intervals(desired_us):

    # Base clock sources (raw frequencies)
    # 24 MHz este frecvența maximă permisă pentru MCLK/SMCLK
    clock_sources = {
        "ACLK": [32768],
        "SMCLK": [2_000_000, 4_000_000, 8_000_000, 12_000_000, 16_000_000, 20_000_000, 24_000_000],
        "MCLK":  [2_000_000, 4_000_000, 8_000_000, 12_000_000, 16_000_000, 20_000_000, 24_000_000]
    }

    # Divizările CS pentru SMCLK și MCLK
    cs_dividers = {
        "DIV1": 1,
        "DIV2": 2,
        "DIV4": 4,
        "DIV8": 8
    }

    # WDT dividers
    wdt_dividers = {
        "2^6": 2**6,
        "2^9": 2**9,
        "2^13": 2**13,
        "2^15": 2**15,
        "2^19": 2**19,
        "2^23": 2**23,
        "2^27": 2**27,
        "2^31": 2**31
    }

    results = []

    for src_name, freqs in clock_sources.items():
        for freq in freqs:

            # ACLK nu are divizări
            if src_name == "ACLK":
                for div_name, div in wdt_dividers.items():
                    t_us = (div / freq) * 1_000_000
                    error = abs(t_us - desired_us)

                    results.append({
                        "source": src_name,
                        "frequency": freq,
                        "cs_divider": "N/A",
                        "divider": div_name,
                        "time_us": t_us,
                        "error_us": error
                    })

            # MCLK și SMCLK — aplicăm divizările CS
            else:
                for cs_name, cs_div in cs_dividers.items():
                    effective_freq = freq / cs_div

                    for div_name, div in wdt_dividers.items():
                        t_us = (div / effective_freq) * 1_000_000
                        error = abs(t_us - desired_us)

                        results.append({
                            "source": f"{src_name} ({cs_name})",
                            "frequency": effective_freq,
                            "cs_divider": cs_name,
                            "divider": div_name,
                            "time_us": t_us,
                            "error_us": error
                        })

    # Alegem combinația cu eroarea minimă
    best = min(results, key=lambda x: x["error_us"])
    return results, best


# ----------------------------
#  STREAMLIT UI
# ----------------------------
st.title("⏱ MSP430 Watchdog Timer Interval Calculator (cu DIVM/DIVS)")
st.write("Calculează intervalele WDT folosind toate divizările posibile din modulul CS (DIVM/DIVS).")

# User input
value = st.number_input("Timp dorit:", min_value=0.0, step=0.1)
unit = st.selectbox("Unitate de timp:", ["ns", "us", "ms", "s"])

if st.button("Calculează"):
    desired_us = to_microseconds(value, unit)
    results, best = compute_wdt_intervals(desired_us)

    st.subheader("Rezultate calculate")

    st.dataframe([
        {
            "Clock Source": r["source"],
            "Frequency (Hz)": r["frequency"],
            "CS Divider": r["cs_divider"],
            "WDT Divider": r["divider"],
            "Time (us)": round(r["time_us"], 3),
            "Error (us)": round(r["error_us"], 3)
        }
        for r in results
    ])

    # Conversii pentru afișare
    best_time_converted = from_microseconds(best['time_us'], unit)
    best_error_converted = from_microseconds(best['error_us'], unit)

    st.subheader("Recomandare optimă")
    st.success(
        f"Sursă: **{best['source']}**\n"
        f"Frecvență rezultată: **{best['frequency']} Hz**\n"
        f"Divizor CS: **{best['cs_divider']}**\n"
        f"Divizor WDT: **{best['divider']}**\n\n"
        f"Timp generat: **{best_time_converted:.6f} {unit}**\n"
        f"Eroare: **{best_error_converted:.6f} {unit}**"
    )
