import React, {useEffect,useState} from "react";

export default function App(){
  const [data,setData]=useState(null);
  const [detalle,setDetalle]=useState([]);

  useEffect(()=>{
    fetch("/api/dashboard").then(r=>r.json()).then(setData);
  },[]);

  const loadDetalle=(c)=>{
    fetch("/api/detail?cliente="+c).then(r=>r.json()).then(setDetalle);
  }

  if(!data) return <div>Cargando...</div>;

  return (
    <div style={{padding:20}}>
      <h1>Dashboard v6</h1>

      <div style={{display:"flex",gap:20}}>
        <div>Equipos: {data.kpis.equipos}</div>
        <div>Alertas: {data.kpis.alertas}</div>
        <div>Reemplazos: {data.kpis.reemplazos}</div>
      </div>

      <h2>Clientes</h2>
      {data.clientes.map(c=>(
        <div key={c.name} onClick={()=>loadDetalle(c.name)} style={{cursor:"pointer"}}>
          {c.name} ({c.total})
        </div>
      ))}

      <h2>Detalle</h2>
      <pre>{JSON.stringify(detalle,null,2)}</pre>
    </div>
  );
}
