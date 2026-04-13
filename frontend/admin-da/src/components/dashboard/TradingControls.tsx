import { useState } from 'react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { ArrowUp, ArrowDown, Plus, X, Info } from '@phosphor-icons/react'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'
import { toast } from 'sonner'
import type { TradeOrder, OrderType, OrderSide } from '@/lib/types'
import { cn } from '@/lib/utils'

interface TradingControlsProps {
  disabled?: boolean
  onOrderSubmit?: (order: TradeOrder) => Promise<void>
}

const POPULAR_SYMBOLS = [
  'BTC/USDT',
  'ETH/USDT',
  'BNB/USDT',
  'SOL/USDT',
  'ADA/USDT'
]

export function TradingControls({ disabled = false, onOrderSubmit }: TradingControlsProps) {
  const [symbol, setSymbol] = useState('BTC/USDT')
  const [customSymbol, setCustomSymbol] = useState('')
  const [showCustomSymbol, setShowCustomSymbol] = useState(false)
  const [side, setSide] = useState<OrderSide>('buy')
  const [orderType, setOrderType] = useState<OrderType>('market')
  const [quantity, setQuantity] = useState('')
  const [price, setPrice] = useState('')
  const [stopPrice, setStopPrice] = useState('')
  const [trailingDelta, setTrailingDelta] = useState('')
  const [trailingPercent, setTrailingPercent] = useState('')
  const [ocoStopPrice, setOcoStopPrice] = useState('')
  const [ocoLimitPrice, setOcoLimitPrice] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const handleSubmit = async () => {
    if (!quantity || parseFloat(quantity) <= 0) {
      toast.error('Invalid Quantity', {
        description: 'Please enter a valid quantity'
      })
      return
    }

    if (orderType === 'limit' && (!price || parseFloat(price) <= 0)) {
      toast.error('Invalid Price', {
        description: 'Limit orders require a price'
      })
      return
    }

    if ((orderType === 'stop_loss' || orderType === 'take_profit') && (!stopPrice || parseFloat(stopPrice) <= 0)) {
      toast.error('Invalid Stop Price', {
        description: 'Stop orders require a stop price'
      })
      return
    }

    if (orderType === 'trailing_stop' && !trailingDelta && !trailingPercent) {
      toast.error('Invalid Trailing Parameters', {
        description: 'Trailing stop requires either delta or percentage'
      })
      return
    }

    if (orderType === 'oco' && (!ocoStopPrice || !ocoLimitPrice)) {
      toast.error('Invalid OCO Parameters', {
        description: 'OCO orders require both stop price and limit price'
      })
      return
    }

    const order: TradeOrder = {
      symbol: showCustomSymbol ? customSymbol : symbol,
      side,
      orderType,
      quantity: parseFloat(quantity),
      ...(orderType === 'limit' && { price: parseFloat(price) }),
      ...(orderType === 'stop_loss' && { stopPrice: parseFloat(stopPrice) }),
      ...(orderType === 'take_profit' && { stopPrice: parseFloat(stopPrice) }),
      ...(orderType === 'trailing_stop' && {
        ...(trailingDelta && { trailingDelta: parseFloat(trailingDelta) }),
        ...(trailingPercent && { trailingPercent: parseFloat(trailingPercent) })
      }),
      ...(orderType === 'oco' && {
        ocoStopPrice: parseFloat(ocoStopPrice),
        ocoLimitPrice: parseFloat(ocoLimitPrice)
      })
    }

    setSubmitting(true)
    try {
      if (onOrderSubmit) {
        await onOrderSubmit(order)
      } else {
        await new Promise(resolve => setTimeout(resolve, 1000))
      }
      
      toast.success('Order Submitted', {
        description: `${side.toUpperCase()} ${quantity} ${order.symbol} (${orderType.replace('_', ' ')})`
      })
      
      setQuantity('')
      setPrice('')
      setStopPrice('')
      setTrailingDelta('')
      setTrailingPercent('')
      setOcoStopPrice('')
      setOcoLimitPrice('')
    } catch (error) {
      toast.error('Order Failed', {
        description: error instanceof Error ? error.message : 'Failed to submit order'
      })
    } finally {
      setSubmitting(false)
    }
  }

  const currentSymbol = showCustomSymbol ? customSymbol : symbol

  return (
    <Card className="p-6">
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h3 className="font-semibold text-lg">Trading Controls</h3>
          {disabled && (
            <span className="text-sm text-warning">Complete checklist to enable</span>
          )}
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <div className="flex gap-2">
            <Button
              onClick={() => setSide('buy')}
              variant={side === 'buy' ? 'default' : 'outline'}
              className={cn(
                'flex-1',
                side === 'buy' && 'bg-success hover:bg-success/90 text-success-foreground'
              )}
              disabled={disabled}
            >
              <ArrowUp className="mr-2" weight="bold" />
              Buy
            </Button>
            <Button
              onClick={() => setSide('sell')}
              variant={side === 'sell' ? 'default' : 'outline'}
              className={cn(
                'flex-1',
                side === 'sell' && 'bg-destructive hover:bg-destructive/90 text-destructive-foreground'
              )}
              disabled={disabled}
            >
              <ArrowDown className="mr-2" weight="bold" />
              Sell
            </Button>
          </div>

          <div className="space-y-2">
            <Label htmlFor="symbol">Symbol</Label>
            {showCustomSymbol ? (
              <div className="flex gap-2">
                <Input
                  id="symbol"
                  placeholder="Enter symbol (e.g., XRP/USDT)"
                  value={customSymbol}
                  onChange={(e) => setCustomSymbol(e.target.value.toUpperCase())}
                  disabled={disabled}
                />
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => {
                    setShowCustomSymbol(false)
                    setCustomSymbol('')
                  }}
                  disabled={disabled}
                >
                  <X />
                </Button>
              </div>
            ) : (
              <div className="flex gap-2">
                <Select
                  value={symbol}
                  onValueChange={setSymbol}
                  disabled={disabled}
                >
                  <SelectTrigger id="symbol" className="flex-1">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {POPULAR_SYMBOLS.map((sym) => (
                      <SelectItem key={sym} value={sym}>
                        {sym}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => setShowCustomSymbol(true)}
                  disabled={disabled}
                  title="Add custom symbol"
                >
                  <Plus size={20} />
                </Button>
              </div>
            )}
          </div>
        </div>

        <Tabs value={orderType} onValueChange={(v) => setOrderType(v as OrderType)} className="w-full">
          <TabsList className="grid w-full grid-cols-3 lg:grid-cols-6">
            <TabsTrigger value="market" disabled={disabled}>Market</TabsTrigger>
            <TabsTrigger value="limit" disabled={disabled}>Limit</TabsTrigger>
            <TabsTrigger value="stop_loss" disabled={disabled}>Stop Loss</TabsTrigger>
            <TabsTrigger value="take_profit" disabled={disabled}>Take Profit</TabsTrigger>
            <TabsTrigger value="trailing_stop" disabled={disabled} className="col-span-1">Trailing</TabsTrigger>
            <TabsTrigger value="oco" disabled={disabled}>OCO</TabsTrigger>
          </TabsList>

          <TabsContent value="market" className="space-y-4 mt-4">
            <div className="space-y-2">
              <Label htmlFor="quantity-market">Quantity</Label>
              <Input
                id="quantity-market"
                type="number"
                step="any"
                min="0"
                placeholder="0.00"
                value={quantity}
                onChange={(e) => setQuantity(e.target.value)}
                disabled={disabled}
                className="font-mono"
              />
            </div>
          </TabsContent>

          <TabsContent value="limit" className="space-y-4 mt-4">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="quantity-limit">Quantity</Label>
                <Input
                  id="quantity-limit"
                  type="number"
                  step="any"
                  min="0"
                  placeholder="0.00"
                  value={quantity}
                  onChange={(e) => setQuantity(e.target.value)}
                  disabled={disabled}
                  className="font-mono"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="price-limit">Limit Price</Label>
                <Input
                  id="price-limit"
                  type="number"
                  step="any"
                  min="0"
                  placeholder="0.00"
                  value={price}
                  onChange={(e) => setPrice(e.target.value)}
                  disabled={disabled}
                  className="font-mono"
                />
              </div>
            </div>
          </TabsContent>

          <TabsContent value="stop_loss" className="space-y-4 mt-4">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="quantity-stop">Quantity</Label>
                <Input
                  id="quantity-stop"
                  type="number"
                  step="any"
                  min="0"
                  placeholder="0.00"
                  value={quantity}
                  onChange={(e) => setQuantity(e.target.value)}
                  disabled={disabled}
                  className="font-mono"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="stop-price">Stop Price</Label>
                <Input
                  id="stop-price"
                  type="number"
                  step="any"
                  min="0"
                  placeholder="0.00"
                  value={stopPrice}
                  onChange={(e) => setStopPrice(e.target.value)}
                  disabled={disabled}
                  className="font-mono"
                />
              </div>
            </div>
          </TabsContent>

          <TabsContent value="take_profit" className="space-y-4 mt-4">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="quantity-tp">Quantity</Label>
                <Input
                  id="quantity-tp"
                  type="number"
                  step="any"
                  min="0"
                  placeholder="0.00"
                  value={quantity}
                  onChange={(e) => setQuantity(e.target.value)}
                  disabled={disabled}
                  className="font-mono"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="tp-price">Take Profit Price</Label>
                <Input
                  id="tp-price"
                  type="number"
                  step="any"
                  min="0"
                  placeholder="0.00"
                  value={stopPrice}
                  onChange={(e) => setStopPrice(e.target.value)}
                  disabled={disabled}
                  className="font-mono"
                />
              </div>
            </div>
          </TabsContent>

          <TabsContent value="trailing_stop" className="space-y-4 mt-4">
            <TooltipProvider>
              <div className="mb-3 flex items-start gap-2 rounded-lg border border-border bg-muted/30 p-3 text-xs">
                <Info size={16} className="mt-0.5 shrink-0 text-accent" weight="duotone" />
                <p className="text-muted-foreground">
                  Trailing stop adjusts automatically as price moves in your favor. Set either a fixed delta or percentage.
                </p>
              </div>
            </TooltipProvider>

            <div className="space-y-2">
              <Label htmlFor="quantity-trailing">Quantity</Label>
              <Input
                id="quantity-trailing"
                type="number"
                step="any"
                min="0"
                placeholder="0.00"
                value={quantity}
                onChange={(e) => setQuantity(e.target.value)}
                disabled={disabled}
                className="font-mono"
              />
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="trailing-delta">Trailing Delta (Optional)</Label>
                <Input
                  id="trailing-delta"
                  type="number"
                  step="any"
                  min="0"
                  placeholder="e.g., 100"
                  value={trailingDelta}
                  onChange={(e) => setTrailingDelta(e.target.value)}
                  disabled={disabled}
                  className="font-mono"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="trailing-percent">Trailing % (Optional)</Label>
                <Input
                  id="trailing-percent"
                  type="number"
                  step="any"
                  min="0"
                  max="100"
                  placeholder="e.g., 2.5"
                  value={trailingPercent}
                  onChange={(e) => setTrailingPercent(e.target.value)}
                  disabled={disabled}
                  className="font-mono"
                />
              </div>
            </div>
          </TabsContent>

          <TabsContent value="oco" className="space-y-4 mt-4">
            <TooltipProvider>
              <div className="mb-3 flex items-start gap-2 rounded-lg border border-border bg-muted/30 p-3 text-xs">
                <Info size={16} className="mt-0.5 shrink-0 text-accent" weight="duotone" />
                <p className="text-muted-foreground">
                  One-Cancels-Other: Set both a limit price (take profit) and stop price (stop loss). When one executes, the other cancels.
                </p>
              </div>
            </TooltipProvider>

            <div className="space-y-2">
              <Label htmlFor="quantity-oco">Quantity</Label>
              <Input
                id="quantity-oco"
                type="number"
                step="any"
                min="0"
                placeholder="0.00"
                value={quantity}
                onChange={(e) => setQuantity(e.target.value)}
                disabled={disabled}
                className="font-mono"
              />
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="oco-limit">Limit Price (Take Profit)</Label>
                <Input
                  id="oco-limit"
                  type="number"
                  step="any"
                  min="0"
                  placeholder="0.00"
                  value={ocoLimitPrice}
                  onChange={(e) => setOcoLimitPrice(e.target.value)}
                  disabled={disabled}
                  className="font-mono"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="oco-stop">Stop Price (Stop Loss)</Label>
                <Input
                  id="oco-stop"
                  type="number"
                  step="any"
                  min="0"
                  placeholder="0.00"
                  value={ocoStopPrice}
                  onChange={(e) => setOcoStopPrice(e.target.value)}
                  disabled={disabled}
                  className="font-mono"
                />
              </div>
            </div>
          </TabsContent>
        </Tabs>

        <Button
          onClick={handleSubmit}
          disabled={disabled || submitting || !currentSymbol}
          className={cn(
            'w-full',
            side === 'buy' && 'bg-success hover:bg-success/90 text-success-foreground',
            side === 'sell' && 'bg-destructive hover:bg-destructive/90 text-destructive-foreground'
          )}
          size="lg"
        >
          {submitting ? 'Submitting...' : `${side === 'buy' ? 'Buy' : 'Sell'} ${currentSymbol || '...'}`}
        </Button>
      </div>
    </Card>
  )
}
