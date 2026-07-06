import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

FIG_W, FIG_H = 12, 6.5
fig = plt.figure(figsize=(FIG_W, FIG_H), facecolor="white")
ax  = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, FIG_W); ax.set_ylim(0, FIG_H); ax.axis("off")

DARK="#1A1A1A"; MID="#555550"; LIGHT="#999990"; RULE="#E8E6E0"

ax.text(FIG_W/2, FIG_H-0.32, "Technical Debt Dataset", ha="center", va="top",
        fontsize=20, fontweight="bold", color=DARK, fontfamily="DejaVu Sans")
ax.text(FIG_W/2, FIG_H-0.72,
        "An empirical dataset of 30 Apache open-source Java projects analysed for technical debt over 20 years",
        ha="center", va="top", fontsize=9.5, color=MID, fontfamily="DejaVu Sans")
ax.axhline(FIG_H-1.02, xmin=0.04, xmax=0.96, color=RULE, linewidth=0.8)

CARDS = [
    ("30","projects","Apache OSS repositories","#3C3489"),
    ("26,106","commit pairs","Refactoring events captured","#712B13"),
    ("362,253","operations","Individual refactoring operations","#0C447C"),
    ("62","types","Distinct refactoring types","#27500A"),
    ("~63K","lines (median)","Codebase size per project","#4A4A4A"),
    ("~1,142 h","median debt","Technical debt per snapshot","#854F0B"),
]
N=len(CARDS); card_w=(FIG_W-0.9)/N; card_h=1.52; card_y=FIG_H-1.14-card_h; gap=0.12; x0=0.45

for i,(val,unit,label,accent) in enumerate(CARDS):
    cx=x0+i*(card_w+gap)
    ax.add_patch(FancyBboxPatch((cx,card_y),card_w,card_h,boxstyle="round,pad=0.06",
        facecolor="#FAFAF8",edgecolor=RULE,linewidth=0.6,zorder=1))
    ax.add_patch(FancyBboxPatch((cx,card_y+card_h-0.07),card_w,0.07,boxstyle="round,pad=0.0",
        facecolor=accent,edgecolor="none",zorder=2))
    ax.text(cx+card_w/2,card_y+card_h-0.42,val,ha="center",va="center",
            fontsize=21,fontweight="bold",color=accent,fontfamily="DejaVu Sans",zorder=3)
    ax.text(cx+card_w/2,card_y+card_h-0.76,unit,ha="center",va="center",
            fontsize=8.5,color=MID,fontfamily="DejaVu Sans",zorder=3)
    ax.axhline(card_y+0.62,xmin=cx/FIG_W,xmax=(cx+card_w)/FIG_W,color=RULE,linewidth=0.6)
    words=label.split()
    if len(words)>3:
        mid=len(words)//2
        ax.text(cx+card_w/2,card_y+0.42," ".join(words[:mid]),ha="center",va="center",
                fontsize=7.8,color=LIGHT,fontfamily="DejaVu Sans",zorder=3)
        ax.text(cx+card_w/2,card_y+0.22," ".join(words[mid:]),ha="center",va="center",
                fontsize=7.8,color=LIGHT,fontfamily="DejaVu Sans",zorder=3)
    else:
        ax.text(cx+card_w/2,card_y+0.32,label,ha="center",va="center",
                fontsize=7.8,color=LIGHT,fontfamily="DejaVu Sans",zorder=3)

CATS=[("TypeChange",6332,"#993C1D"),("Structural",4922,"#185FA5"),("Signature",4344,"#3B6D11"),
      ("Modifier",4280,"#854F0B"),("Rename",3682,"#534AB7"),("Move",1688,"#0F6E56"),("Other",858,"#888780")]
chart_x=0.45; chart_y=0.52; chart_w=FIG_W-0.90; chart_h=card_y-chart_y-0.22
max_val=max(c[1] for c in CATS); bar_gap=0.06; bar_w=(chart_w-bar_gap*(len(CATS)-1))/len(CATS)

ax.text(FIG_W/2,chart_y+chart_h+0.14,"Refactoring commits by category",
        ha="center",va="bottom",fontsize=9,color=MID,fontfamily="DejaVu Sans")

for i,(cat,count,color) in enumerate(CATS):
    bx=chart_x+i*(bar_w+bar_gap); bh=(count/max_val)*chart_h
    ax.add_patch(FancyBboxPatch((bx,chart_y),bar_w,bh,boxstyle="round,pad=0.04",
        facecolor=color,edgecolor="none",alpha=0.85,zorder=2))
    ax.text(bx+bar_w/2,chart_y+bh+0.05,f"{count:,}",ha="center",va="bottom",
            fontsize=7.5,fontweight="bold",color=color,fontfamily="DejaVu Sans")
    ax.text(bx+bar_w/2,chart_y-0.08,cat,ha="center",va="top",
            fontsize=7.5,color=MID,fontfamily="DejaVu Sans")

ax.text(FIG_W/2,0.18,
        "Lenarduzzi, Saarimäki, Taibi (2019)  ·  Tools: SonarQube, RefactoringMiner, PyDriller  ·  2000 – 2021",
        ha="center",va="top",fontsize=7.5,color="#BBBBBB",fontfamily="DejaVu Sans")

plt.savefig("dataset_summary.png",dpi=150,bbox_inches="tight",facecolor="white",edgecolor="none")
plt.close()
print("Saved: dataset_summary.png")