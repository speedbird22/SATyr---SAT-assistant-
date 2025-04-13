# Bujji
May this code achieve what it seeks, to asisst those who are preparing for SAT's, may this code be a guiding light for those who seem to be lost and have no path to go on, may this code abide by our motto - for God and country.

<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Change Font Size</title>
  <style>
    #text {
      font-size: 16px;
      margin-top: 20px;
    }
  </style>
</head>
<body>
  <h2>Change Font Size</h2>

  <label for="fontSizeSelector">Select Font Size:</label>
  <select id="fontSizeSelector">
    <option value="12px">12px</option>
    <option value="16px" selected>16px</option>
    <option value="20px">20px</option>
    <option value="24px">24px</option>
    <option value="30px">30px</option>
  </select>

  <p id="text">
    This is the sample text. You can change its font size using the dropdown above.
  </p>

  <script>
    const selector = document.getElementById("fontSizeSelector");
    const text = document.getElementById("text");

    selector.addEventListener("change", function() {
      text.style.fontSize = this.value;
    });
  </script>
</body>
</html>















































