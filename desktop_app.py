import sys, json, math
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import numpy as np

APP_VERSION="0.99-win"

EQUATIONS=[
("MEXIANA_HIST","Amazônia","Várzea estuarina - FOD Aluvial/Terras Baixas","B = 0,1184 × DAP^2,53","Inventário Fazenda Santo Ambrósio"),
("CHAVE2014_DHRHO","Florestas tropicais","Domínio deve ser verificado","B = 0,0673 × (ρ × D² × H)^0,976","Chave et al. 2014"),
("SAMPAIO2005_CAAT_DAP9","Caatinga","DAP ≤ 30 cm","B = 0,173 × DAP^2,295","Sampaio & Silva 2005"),
("RIBEIRO2011_CSS_D_WD","Cerrado","Cerrado sensu stricto","ln(B) = -3,3520 + 2,9853 ln(DAP) + 1,1855 ln(ρ)","Ribeiro et al. 2011"),
("BURGER2008_MA_D","Mata Atlântica","Floresta Atlântica","ln(B) = -3,068 + 2,522 ln(DAP)","Burger & Delitti 2008"),
]

def agb_mexiana(dbh_cm):
    return 0.1184*np.power(np.asarray(dbh_cm,dtype=float),2.53)

def load_inventory(path):
    df=pd.read_excel(path,sheet_name="Biomassa árvores vivas",usecols="A:E")
    df.columns=["plot","tree","dbh_m","height_m","species"]
    df["plot"]=df["plot"].ffill()
    df=df[df["tree"].notna() & df["dbh_m"].notna()].copy()
    df["dbh_cm"]=pd.to_numeric(df["dbh_m"],errors="coerce")*100
    df["height_m"]=pd.to_numeric(df["height_m"],errors="coerce")
    return df[df["dbh_cm"].between(10,400)].copy()

def summarize_inventory(df,plot_area_m2=250):
    d=df.copy(); d["agb_kg"]=agb_mexiana(d["dbh_cm"])
    p=d.groupby("plot",as_index=False)["agb_kg"].sum()
    x=(p["agb_kg"]/1000*(10000/plot_area_m2)).to_numpy(float)
    n=len(x); mean=float(np.mean(x)); sd=float(np.std(x,ddof=1)); se=sd/math.sqrt(n)
    return n,mean,max(0,mean-1.96*se),mean+1.96*se

def self_test():
    assert abs(float(agb_mexiana(10))-0.1184*(10**2.53))<1e-8
    assert abs(100*0.47-47)<1e-9
    assert len(EQUATIONS)>=5
    print("ENFORM_VERDE_SELF_TEST_OK")

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"Enform Verde {APP_VERSION}")
        self.geometry("1100x720"); self.minsize(900,600)
        self.project={"version":APP_VERSION}; self.inv=None
        self._style(); self._ui()
    def _style(self):
        s=ttk.Style(self)
        try:s.theme_use("vista")
        except:pass
        s.configure("Title.TLabel",font=("Segoe UI",18,"bold"))
        s.configure("H.TLabel",font=("Segoe UI",11,"bold"))
        s.configure("TButton",padding=7)
    def _ui(self):
        top=ttk.Frame(self,padding=(18,14)); top.pack(fill="x")
        ttk.Label(top,text="Enform Verde",style="Title.TLabel").pack(side="left")
        ttk.Label(top,text="  Biomassa e carbono florestal",foreground="#555").pack(side="left",pady=(7,0))
        ttk.Button(top,text="Salvar projeto",command=self.save_project).pack(side="right")
        self.nb=ttk.Notebook(self); self.nb.pack(fill="both",expand=True,padx=18,pady=(0,18))
        names=["1. Projeto","2. Vegetação","3. Inventário / AGB","4. Resultados","5. Biblioteca científica"]
        self.tabs=[]
        for n in names:
            f=ttk.Frame(self.nb,padding=18); self.nb.add(f,text=n); self.tabs.append(f)
        self.project_tab(); self.veg_tab(); self.inventory_tab(); self.results_tab(); self.library_tab()
        self.status=tk.StringVar(value="Pronto.")
        ttk.Label(self,textvariable=self.status,relief="sunken",anchor="w",padding=5).pack(fill="x",side="bottom")
    def project_tab(self):
        f=self.tabs[0]
        ttk.Label(f,text="Projeto",style="H.TLabel").grid(row=0,column=0,columnspan=2,sticky="w",pady=(0,12))
        ttk.Label(f,text="Nome").grid(row=1,column=0,sticky="w")
        self.name=tk.StringVar(value="Projeto Enform Verde")
        ttk.Entry(f,textvariable=self.name,width=60).grid(row=1,column=1,sticky="ew",padx=10)
        ttk.Label(f,text="Código CAR").grid(row=2,column=0,sticky="w",pady=10)
        self.car=tk.StringVar(); ttk.Entry(f,textvariable=self.car,width=60).grid(row=2,column=1,sticky="ew",padx=10)
        ttk.Label(f,text="O código CAR é registrado, mas o programa não inventa nem resolve automaticamente o perímetro.",foreground="#666").grid(row=3,column=1,sticky="w",padx=10)
        ttk.Label(f,text="Arquivo vetorial").grid(row=4,column=0,sticky="w",pady=(20,5))
        ttk.Button(f,text="Selecionar KML / GeoJSON / SHP / GPKG",command=self.pick_vector).grid(row=4,column=1,sticky="w",padx=10,pady=(20,5))
        self.vector=tk.StringVar(value="Nenhum arquivo selecionado")
        ttk.Label(f,textvariable=self.vector).grid(row=5,column=1,sticky="w",padx=10)
        f.columnconfigure(1,weight=1)
    def veg_tab(self):
        f=self.tabs[1]; ttk.Label(f,text="Bioma e fitofisionomia",style="H.TLabel").pack(anchor="w")
        r=ttk.Frame(f); r.pack(fill="x",pady=15)
        ttk.Label(r,text="Bioma").grid(row=0,column=0,sticky="w")
        self.biome=tk.StringVar(value="Amazônia")
        ttk.Combobox(r,textvariable=self.biome,state="readonly",values=["Amazônia","Mata Atlântica","Cerrado","Caatinga"],width=28).grid(row=0,column=1,padx=10)
        ttk.Label(r,text="Fitofisionomia").grid(row=1,column=0,sticky="w",pady=12)
        self.phys=tk.StringVar(value="Várzea estuarina - FOD Aluvial/Terras Baixas")
        ttk.Entry(r,textvariable=self.phys,width=70).grid(row=1,column=1,padx=10,sticky="ew"); r.columnconfigure(1,weight=1)
        ttk.Label(f,text="A equação deve ser escolhida somente após verificar domínio de calibração, DAP, altura, densidade da madeira e fitofisionomia.",foreground="#555").pack(anchor="w")
    def inventory_tab(self):
        f=self.tabs[2]; ttk.Label(f,text="Inventário e biomassa aérea",style="H.TLabel").pack(anchor="w")
        ttk.Button(f,text="Carregar inventário XLSX de Mexiana",command=self.open_inventory).pack(anchor="w",pady=12)
        self.inv_lbl=tk.StringVar(value="Nenhum inventário carregado"); ttk.Label(f,textvariable=self.inv_lbl).pack(anchor="w")
        self.qa=tk.Text(f,height=17,wrap="word"); self.qa.pack(fill="both",expand=True,pady=12)
        self.qa.insert("1.0","O resumo do inventário aparecerá aqui."); self.qa.config(state="disabled")
    def results_tab(self):
        f=self.tabs[3]; ttk.Label(f,text="Resultados",style="H.TLabel").pack(anchor="w")
        self.res=tk.Text(f,height=22,wrap="word"); self.res.pack(fill="both",expand=True,pady=12)
        self.res.insert("1.0","Nenhum resultado calculado."); self.res.config(state="disabled")
    def library_tab(self):
        f=self.tabs[4]; ttk.Label(f,text="Biblioteca científica — equações parametrizadas",style="H.TLabel").pack(anchor="w")
        box=tk.Text(f,height=24,wrap="word"); box.pack(fill="both",expand=True,pady=10)
        for i,b,p,e,src in EQUATIONS:
            box.insert("end",f"{i} | {b} | {p}\n{e}\nFonte: {src}\n\n")
        box.config(state="disabled")
    def pick_vector(self):
        p=filedialog.askopenfilename(filetypes=[("Vetores","*.kml *.geojson *.json *.shp *.gpkg"),("Todos","*.*")])
        if p:self.vector.set(p); self.project["vector"]=p
    def open_inventory(self):
        p=filedialog.askopenfilename(filetypes=[("Excel","*.xlsx")])
        if not p:return
        try:
            d=load_inventory(p); n,mean,lo,hi=summarize_inventory(d)
            issues=[]
            if d["height_m"].isna().any():issues.append("alturas ausentes")
            if (d["height_m"].fillna(1)<=0).any():issues.append("alturas não positivas")
            self.inv=d; self.project["inventory"]=p; self.inv_lbl.set(Path(p).name)
            txt=f"Árvores válidas: {len(d):,}\nParcelas: {n}\nQA: {', '.join(issues) if issues else 'sem alertas básicos'}\n\nAGB — equação histórica Mexiana\nMédia: {mean:,.2f} Mg/ha\nIC95% amostral aproximado: {lo:,.2f} – {hi:,.2f} Mg/ha\n\nA equação histórica de Mexiana não deve ser transferida automaticamente para outras fitofisionomias."
            self.qa.config(state="normal"); self.qa.delete("1.0","end"); self.qa.insert("1.0",txt); self.qa.config(state="disabled")
            c=mean*0.47; co2=c*(44/12)
            out=f"Biomassa aérea (AGB): {mean:,.2f} Mg/ha\nCarbono da AGB (fração 0,47): {c:,.2f} Mg C/ha\nEquivalente de CO₂ da AGB: {co2:,.2f} tCO₂e/ha\n\nOs demais compartimentos (BGB, necromassa, serrapilheira e solo) permanecem não estimados até receberem dados/métodos próprios. Não são preenchidos silenciosamente."
            self.res.config(state="normal"); self.res.delete("1.0","end"); self.res.insert("1.0",out); self.res.config(state="disabled")
            self.status.set("Inventário carregado e AGB calculada.")
        except Exception as e: messagebox.showerror("Enform Verde",str(e))
    def save_project(self):
        self.project.update({"name":self.name.get(),"car":self.car.get(),"biome":self.biome.get(),"physiognomy":self.phys.get()})
        p=filedialog.asksaveasfilename(defaultextension=".enformverde.json",filetypes=[("Projeto Enform Verde","*.enformverde.json")])
        if p:Path(p).write_text(json.dumps(self.project,ensure_ascii=False,indent=2),encoding="utf-8"); self.status.set("Projeto salvo.")

if __name__=="__main__":
    if "--self-test" in sys.argv:self_test()
    else:App().mainloop()
