<?php

use Illuminate\Http\Request;

/*
|--------------------------------------------------------------------------
| API Routes
|--------------------------------------------------------------------------
|
| Here is where you can register API routes for your application. These
| routes are loaded by the RouteServiceProvider within a group which
| is assigned the "api" middleware group. Enjoy building your API!
|
*/

Route::group([
    'prefix' => 'weather'
], function() {
    Route::get("now", [
        'as' => 'api.weather.now',
        'uses' => 'Api\WeatherController@getNow'
    ]);
    
    Route::get('daily', [
        'as' => 'api.weather.daily',
        'uses' => 'Api\WeatherController@getDaily'
    ]);
    
    Route::get('weekly', [
        'as' => 'api.weather.weekly',
        'uses' => 'Api\WeatherController@getWeekly'
    ]);
    
    Route::get('monthly', [
        'as' => 'api.weather.monthly',
        'uses' => 'Api\WeatherController@getMonthly'
    ]);
    
});

Route::group([
    'prefix' => 'water-temp'
], function() {

    Route::get('now', [
        'as' => 'api.water-temp.now',
        'uses' => 'Api\WaterTempController@getNow'
    ]);
    
    Route::get('daily', [
        'as' => 'api.water-temp.daily',
        'uses' => 'Api\WaterTempController@getDaily'
    ]);
    
    Route::get('weekly', [
        'as' => 'api.water-temp.weekly',
        'uses' => 'Api\WaterTempController@getWeekly'
    ]);
    
    Route::get('monthly', [
        'as' => 'api.water-temp.monthly',
        'uses' => 'Api\WaterTempController@getMonthly'
    ]);

    Route::group([
        'prefix' => 'graph'
    ], function() {
        
        Route::get('daily', [
            'as' => 'api.weather.graph.daily',
            'uses' => 'Api\Graph\WaterTempController@getDaily'
        ]);
        
    });
});


