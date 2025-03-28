var options = {
	chart: {
		height: 320,
		type: "area",
		toolbar: {
			show: false,
		},
		dropShadow: {
			enabled: true,
			opacity: 0.1,
			blur: 5,
			left: -10,
			top: 10,
		},
	},
	dataLabels: {
		enabled: false,
	},
	stroke: {
		curve: "smooth",
		width: 3,
	},
	series: [
		{
			name: "Added",
			data: [300, 200, 400, 300, 500, 400, 600],
		},
		{
			name: "Converted",
			data: [150, 100, 200, 150, 250, 200, 300],
		},
	],
	grid: {
		borderColor: "#414144",
		strokeDashArray: 5,
		xaxis: {
			lines: {
				show: true,
			},
		},
		yaxis: {
			lines: {
				show: false,
			},
		},
		padding: {
			top: 0,
			right: 30,
			bottom: 0,
			left: 30,
		},
	},
	xaxis: {
		type: "day",
		categories: ["New", "Mid", "Long", "Short", "Low", "High", "Best"],
	},
	colors: ["#46484d", "#ba1654", "#EEEEEE", "#CCCCCC", "#ba1654", "#111111"],
	yaxis: {
		show: false,
	},
	markers: {
		size: 0,
		opacity: 0.2,
		colors: ["#46484d", "#ba1654", "#EEEEEE", "#CCCCCC", "#ba1654", "#111111"],
		strokeColor: "#fff",
		strokeWidth: 2,
		hover: {
			size: 7,
		},
	},
	tooltip: {
		x: {
			format: "dd/MM/yy",
		},
	},
};

var chart = new ApexCharts(document.querySelector("#leads"), options);

chart.render();
