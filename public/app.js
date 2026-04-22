const API = "/api";

function getToken() {
  return localStorage.getItem("token");
}

async function login() {
  const nome = document.getElementById("nome").value;
  const password = document.getElementById("password").value;

  const res = await fetch(API + "/login", {
    method: "POST",
    body: JSON.stringify({ nome, password })
  });

  const data = await res.json();
  localStorage.setItem("token", data.token);

  window.location = "/dashboard.html";
}

async function loadDispositivi() {
  const res = await fetch(API + "/dispositivi", {
    headers: {
      Authorization: "Bearer " + getToken()
    }
  });

  const data = await res.json();

  const ul = document.getElementById("lista");
  ul.innerHTML = "";

  data.forEach(d => {
    const li = document.createElement("li");
    li.innerText = d.nome;
    ul.appendChild(li);
  });
}

async function invia() {
  const id = document.getElementById("id_dispositivo").value;
  const valore = document.getElementById("valore").value;

  await fetch(API + "/letture", {
    method: "POST",
    headers: {
      Authorization: "Bearer " + getToken()
    },
    body: JSON.stringify({
      id_dispositivo: id,
      valore_numerico: valore
    })
  });

  alert("Inviato");
}