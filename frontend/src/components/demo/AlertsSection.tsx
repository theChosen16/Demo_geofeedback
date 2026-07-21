import React from 'react'

interface AlertsSectionProps {
  user: any
  userAlerts: any[]
  selectedLocation: any
  selectedApproach: string
  isSettingAlert: boolean
  setIsSettingAlert: (val: boolean) => void
  alertTriggerType: string
  setAlertTriggerType: (val: string) => void
  alertTriggerValue: number
  setAlertTriggerValue: (val: number) => void
  alertFrequency: string
  setAlertFrequency: (val: string) => void
  isSavingAlert: boolean
  handleCreateAlert: () => void
  handleDeleteAlert: (alertId: number) => void
}

export const AlertsSection: React.FC<AlertsSectionProps> = ({
  user,
  userAlerts,
  selectedLocation,
  selectedApproach,
  isSettingAlert,
  setIsSettingAlert,
  alertTriggerType,
  setAlertTriggerType,
  alertTriggerValue,
  setAlertTriggerValue,
  alertFrequency,
  setAlertFrequency,
  isSavingAlert,
  handleCreateAlert,
  handleDeleteAlert,
}) => {
  return (
    <div className="glass-panel p-6 rounded-xl flex flex-col gap-4 text-left">
      <div className="flex items-center justify-between">
        <h4 className="flex items-center gap-2 text-white font-bold text-sm font-outfit">
          <i className="fas fa-bell text-teal-400 text-sm"></i>
          Monitoreo y Alertas Territoriales
        </h4>
        {userAlerts.length > 0 && !isSettingAlert && selectedLocation && selectedApproach && (
          <button
            onClick={() => setIsSettingAlert(true)}
            className="btn btn-xs btn-outline text-teal-400 border-teal-500/30 hover:bg-teal-500/10 rounded-lg text-[10px] font-bold"
          >
            + Nueva Alerta
          </button>
        )}
      </div>

      {user ? (
        <div className="flex flex-col gap-3">
          {userAlerts.length > 0 ? (
            userAlerts.map((alertItem) => (
              <div
                key={alertItem.id}
                className="bg-[#111318]/60 border border-white/5 p-3 rounded-xl flex flex-col gap-2"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-white truncate max-w-[170px]">
                    {alertItem.location_name}
                  </span>
                  <button
                    onClick={() => handleDeleteAlert(alertItem.id)}
                    className="text-[10px] text-red-400 hover:text-red-300 font-bold"
                  >
                    Eliminar
                  </button>
                </div>
                <div className="text-[10px] text-gray-400 flex flex-col gap-0.5">
                  <div>Condición: <span className="text-teal-400 font-semibold">{alertItem.trigger_type}</span> ({alertItem.trigger_value})</div>
                  <div>Frecuencia: <span className="text-gray-300">{alertItem.frequency === 'daily' ? 'Diaria' : 'Semanal'}</span></div>
                  {alertItem.last_index_value !== null && alertItem.last_index_value !== undefined && (
                    <div>Último Valor: <span className="text-gray-300 font-mono">{alertItem.last_index_value.toFixed(4)}</span></div>
                  )}
                </div>
              </div>
            ))
          ) : (
            <div className="text-center py-2">
              <p className="text-xs text-gray-500 mb-3 font-semibold">No tienes alertas configuradas.</p>
              {selectedLocation && selectedApproach && !isSettingAlert && (
                <button
                  onClick={() => setIsSettingAlert(true)}
                  className="btn btn-xs btn-outline btn-primary text-teal-400 hover:bg-teal-500/10 hover:text-teal-300 rounded-lg w-full font-bold"
                >
                  🔔 Activar Monitoreo en esta Zona
                </button>
              )}
            </div>
          )}

          {isSettingAlert && selectedLocation && selectedApproach && (
            <div className="bg-[#111318] border border-teal-500/20 p-4 rounded-xl flex flex-col gap-3">
              <div className="text-xs font-bold text-white">Configurar Alerta</div>
              
              <div className="flex flex-col gap-1">
                <span className="text-[9px] text-gray-400 font-semibold">Condición Disparadora</span>
                <select
                  value={alertTriggerType}
                  onChange={(e) => setAlertTriggerType(e.target.value)}
                  className="select select-xs bg-[#16171d] border-white/10 text-white rounded text-[10px] w-full"
                >
                  <option value="ndvi_below">NDVI (Vegetación) menor que</option>
                  <option value="ndwi_above">NDWI (Inundación/Agua) mayor que</option>
                  <option value="ndmi_below">NDMI (Humedad Suelo) menor que</option>
                  <option value="ndvi_drop_pct">Caída de NDVI (%) mayor o igual a</option>
                </select>
              </div>

              <div className="flex flex-col gap-1">
                <span className="text-[9px] text-gray-400 font-semibold">Frecuencia de Monitoreo</span>
                <select
                  value={alertFrequency}
                  onChange={(e) => setAlertFrequency(e.target.value)}
                  className="select select-xs bg-[#16171d] border-white/10 text-white rounded text-[10px] w-full"
                >
                  <option value="daily">Monitoreo Diario</option>
                  <option value="weekly">Monitoreo Semanal</option>
                </select>
              </div>

              <div className="flex flex-col gap-1">
                <span className="text-[9px] text-gray-400 font-semibold">Valor de Umbral</span>
                <input
                  type="number"
                  step="0.01"
                  value={alertTriggerValue}
                  onChange={(e) => setAlertTriggerValue(Number(e.target.value))}
                  className="input input-xs bg-[#16171d] border-white/10 text-white rounded text-[10px]"
                />
              </div>

              <div className="flex gap-2 mt-1">
                <button
                  onClick={handleCreateAlert}
                  disabled={isSavingAlert}
                  className="btn btn-xs btn-primary flex-1 rounded-lg font-bold"
                >
                  {isSavingAlert ? 'Guardando...' : 'Crear Alerta'}
                </button>
                <button
                  onClick={() => setIsSettingAlert(false)}
                  className="btn btn-xs btn-ghost text-gray-400 flex-1 rounded-lg font-bold"
                >
                  Cancelar
                </button>
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="flex flex-col gap-2 bg-[#111318]/40 border border-white/5 p-4 rounded-xl text-xs">
          <div className="text-gray-400 font-semibold leading-relaxed">
            💡 <span className="text-white font-bold">Monitoreo Semanal Satelital (Premium):</span> Guarda un punto de interés para vigilar variaciones críticas de sequía o vegetación y recibir alertas automáticas por email.
          </div>
          <div className="text-gray-500 font-semibold text-[10px] mt-1">
            Inicia sesión con Google para acceder a esta prueba gratuita del plan premium.
          </div>
        </div>
      )}
    </div>
  )
}
