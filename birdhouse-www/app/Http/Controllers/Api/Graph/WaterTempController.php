<?php

namespace App\Http\Controllers\Api\Graph;

use App\Http\Controllers\Controller;
use App\Models\WaterTemp;
use Carbon\Carbon;
class WaterTempController extends Controller
{
    public function getDaily()
    {
        $waterTemps = WaterTemp::orderBy('recorded_at', 'desc')
                               ->whereBetween('recorded_at', [Carbon::now()->startOfDay(), Carbon::now()])
                               ->pluck('temperature', 'recorded_at');
        
        $graph = new \ezcGraphLineChart();
        
        $graph->options->fillLines = 210;
        $graph->title = 'Water Temperature';
        $graph->legend = false;
        
        $graph->xAxis = new \ezcGraphChartElementDateAxis();
        
        $graph->data['Water Temp'] = new \ezcGraphArrayDataSet($waterTemps);
        
        $graph->renderToOutput(640, 480);
    }
}