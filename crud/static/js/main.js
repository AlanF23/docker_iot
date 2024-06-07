
const btnDelete= document.querySelectorAll('.btn-borrar');
if(btnDelete) {
  const btnArray = Array.from(btnDelete);
  btnArray.forEach((btn) => {
    btn.addEventListener('click', (e) => {
      if(!confirm('¿Está seguro de querer borrar?')){
        e.preventDefault();
      }
    });
  })
}

document.addEventListener('DOMContentLoaded', function () {
  const themeSelector = document.getElementById('themeSelector');
  const currentTheme = localStorage.getItem('theme') || 'dark';
  
  document.getElementById('themeStylesheet').setAttribute('href', `https://bootswatch.com/5/${currentTheme}/bootstrap.min.css`);
  themeSelector.value = currentTheme;

  themeSelector.addEventListener('change', function () {
    const selectedTheme = themeSelector.value;
    localStorage.setItem('theme', selectedTheme);
    document.getElementById('themeStylesheet').setAttribute('href', `https://bootswatch.com/5/${selectedTheme}/bootstrap.min.css`);
  });
});