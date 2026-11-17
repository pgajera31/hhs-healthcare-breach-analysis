from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title='HHS Cyber Risk | Team 8',page_icon='🛡️',layout='wide')
H='Hacking/IT Incident'; U='Unauthorized Access/Disclosure'
COLORS={H:'#2563eb',U:'#f97316'}
@st.cache_data
def load():
 d=pd.read_csv(Path(__file__).parent/'hhs_team8_cleaned.csv',parse_dates=['Breach Submission Date'])
 d['Year']=d['Breach Submission Date'].dt.year
 return d
base=load()
st.title('Healthcare Cyber Risk Intelligence')
st.caption('Team 8 · Hacking/IT Incidents vs. Unauthorized Access/Disclosure · HHS OCR reported breaches · Submission dates: Jan 2020–Nov 10, 2026')
st.markdown('**Research question:** How do hacking/IT incidents and unauthorized access or disclosure differ in their reported patterns and consequences?')
with st.sidebar:
 st.header('Explore the data')
 years=st.slider('Date range (submission year)',2020,2026,(2020,2026),1)
 state=st.selectbox('State',['All states']+sorted(base['State'].dropna().unique().tolist()))
 entity=st.selectbox('Covered entity type',['All entity types']+sorted(base['Covered Entity Type'].dropna().unique().tolist()))
 st.caption('Filters update every metric and chart. The 2026 data stops on November 10.')
df=base[base['Year'].between(*years)].copy()
if state!='All states':df=df[df['State']==state]
if entity!='All entity types':df=df[df['Covered Entity Type']==entity]
if df.empty:
 st.warning('No records match these filters. Try expanding the date range or changing a dropdown.');st.stop()
agg=df.groupby('Type of Breach').agg(Breaches=('Individuals Affected','size'),Affected=('Individuals Affected','sum'),Median=('Individuals Affected','median')).reindex([H,U],fill_value=0).reset_index()
metrics=st.columns(4)
metrics[0].metric('Reported breaches',f'{len(df):,}')
metrics[1].metric('Individuals affected (reported)',f'{df["Individuals Affected"].sum():,}')
metrics[2].metric('Hacking incidents',f'{(df["Type of Breach"]==H).sum():,}')
metrics[3].metric('Unauthorized disclosures',f'{(df["Type of Breach"]==U).sum():,}')
st.subheader('1 · Side-by-side impact')
measure=st.radio('Bar chart measure',['Reported individuals affected','Breach count','Median affected per breach'],horizontal=True)
key={'Reported individuals affected':'Affected','Breach count':'Breaches','Median affected per breach':'Median'}[measure]
fig=px.bar(agg,x='Type of Breach',y=key,color='Type of Breach',color_discrete_map=COLORS,text_auto=',.0f',labels={'Type of Breach':'Incident type',key:measure})
fig.update_layout(showlegend=False,xaxis_title=None,margin=dict(t=15,b=10))
st.plotly_chart(fig,use_container_width=True)
st.caption('Median is less sensitive to exceptionally large breaches than the total or mean. Individuals affected are reported counts, not unique persons across breaches.')
st.subheader('2 · Reported incidents over time')
trend=df.groupby(['Year','Type of Breach'],as_index=False).agg(Breaches=('Individuals Affected','size'),Affected=('Individuals Affected','sum'))
trend_metric=st.radio('Line chart measure',['Breach count','Individuals affected'],horizontal=True)
y='Breaches' if trend_metric=='Breach count' else 'Affected'
fig=px.line(trend,x='Year',y=y,color='Type of Breach',markers=True,color_discrete_map=COLORS,labels={y:trend_metric,'Type of Breach':'Incident type'})
fig.update_xaxes(dtick=1);fig.update_layout(margin=dict(t=15,b=10));st.plotly_chart(fig,use_container_width=True)
st.caption('2026 is incomplete; do not interpret its total as a full-year decline. Submission dates are not necessarily incident dates.')
st.subheader('3 · Where breached information was located')
left,right=st.columns(2)
for col,kind in [(left,H),(right,U)]:
 sub=df[df['Type of Breach']==kind]
 # Multi-location records are counted once per listed location; slices reflect mentions, not mutually exclusive incidents.
 locations=sub['Location of Breached Information'].fillna('').str.split(',').explode().str.strip()
 locations=locations[locations.ne('')].value_counts().reset_index()
 locations.columns=['Location','Mentions']
 with col:
  st.markdown(f'**{kind}**')
  if locations.empty:st.info('No location values for this selection.')
  else:
   fig=px.pie(locations,names='Location',values='Mentions',hole=.4)
   fig.update_traces(textposition='inside',textinfo='percent',hovertemplate='%{label}: %{value:,} location mentions (%{percent})<extra></extra>')
   fig.update_layout(legend=dict(orientation='h',y=-.15),margin=dict(t=10,b=30))
   st.plotly_chart(fig,use_container_width=True)
st.caption('A single report can list multiple information locations. Pie slices show the share of location mentions within each incident type, not the share of unique breaches or affected individuals.')
st.subheader('Comparison table')
st.dataframe(agg.rename(columns={'Type of Breach':'Breach type','Breaches':'Reported breaches','Affected':'Reported individuals affected','Median':'Median individuals affected'}),hide_index=True,use_container_width=True)
with st.expander('Evidence-based risk interpretation and recommendations',expanded=True):
 st.markdown('''**Finding 1 — Scale:** Across the full reporting period, hacking/IT incidents have higher reported breach counts and a much higher combined affected-individual count than unauthorized access/disclosure. **Action:** Prioritize phishing-resistant MFA, patch management, and continuous monitoring of internet-facing and internal systems.\n\n**Finding 2 — Typical incident size:** The median reported hacking incident affects more individuals than the median unauthorized access/disclosure incident. **Action:** Apply least-privilege access, network segmentation, and tested incident response procedures to reduce the reach and duration of compromise.\n\n**Finding 3 — Different exposure locations:** Network servers dominate hacking location mentions; paper records and email are prominent in unauthorized access/disclosure. **Action:** Combine server security and email controls with role-based access, staff training, and secure paper-record handling.\n\n**Important:** These controls are risk-management recommendations, not interventions whose effectiveness can be proven from this dataset.''')
with st.expander('Data preparation, scope and limitations'):
 st.markdown('''- Source: user-supplied merged HHS OCR breach workbook; no live portal updates are included.\n- Scope: breach submission dates from January 1, 2020 through November 10, 2026, inclusive.\n- Comparison: only exact categories `Hacking/IT Incident` and `Unauthorized Access/Disclosure`; other breach categories are excluded from the two-category comparison.\n- Cleaning: parsed submission dates, standardized field whitespace, parsed individuals affected as nonnegative integers, retained source rows without automatic deduplication. The cleaned extract excludes free-text web descriptions.\n- Reports may be submitted later than the incident occurred; 2026 is a partial year.\n- This dataset covers reported HHS OCR breaches, not all cybersecurity incidents; reporting rules and practices affect coverage.\n- Individuals-affected counts are incident-level reported values, not deduplicated unique people, confirmed harm, financial loss, or causal evidence.\n- Breach types and information locations reflect reported classifications; locations can be multiple per incident.\n- Extreme incidents can dominate totals; use median and incident counts for context.\n- No exposure denominator (such as number of healthcare organizations) is available to calculate true incident rates.''')
