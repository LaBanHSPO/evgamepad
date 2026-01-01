/**
 * Example component demonstrating Socket.IO trading operations
 * Shows how to use the useTrading hook for login, buy, sell, modify, and close
 */

import React, { useState } from 'react';
import { useTrading } from '@/hooks/useTrading';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';

export const TradingExample: React.FC = () => {
  const {
    isConnected,
    isLoggedIn,
    accountInfo,
    loading,
    error,
    login,
    buy,
    sell,
    modify,
    close,
    clearError,
  } = useTrading();

  // Login form
  const [loginForm, setLoginForm] = useState({
    account: '',
    password: '',
    server: '',
  });

  // Order form
  const [orderForm, setOrderForm] = useState({
    symbol: 'EURUSD',
    volume: '0.01',
    sl: '',
    tp: '',
  });

  // Modify form
  const [modifyForm, setModifyForm] = useState({
    ticket: '',
    sl: '',
    tp: '',
  });

  // Close form
  const [closeTicket, setCloseTicket] = useState('');

  // Handlers
  const handleLogin = async () => {
    try {
      const result = await login({
        account: parseInt(loginForm.account),
        password: loginForm.password,
        server: loginForm.server,
      });
      console.log('Login successful:', result);
    } catch (err) {
      console.error('Login failed:', err);
    }
  };

  const handleBuy = async () => {
    try {
      const result = await buy({
        symbol: orderForm.symbol,
        volume: parseFloat(orderForm.volume),
        sl: orderForm.sl ? parseFloat(orderForm.sl) : undefined,
        tp: orderForm.tp ? parseFloat(orderForm.tp) : undefined,
      });
      console.log('Buy order placed:', result);
      alert(`Buy order successful! Ticket: ${result.ticket}, Price: ${result.price}`);
    } catch (err) {
      console.error('Buy failed:', err);
    }
  };

  const handleSell = async () => {
    try {
      const result = await sell({
        symbol: orderForm.symbol,
        volume: parseFloat(orderForm.volume),
        sl: orderForm.sl ? parseFloat(orderForm.sl) : undefined,
        tp: orderForm.tp ? parseFloat(orderForm.tp) : undefined,
      });
      console.log('Sell order placed:', result);
      alert(`Sell order successful! Ticket: ${result.ticket}, Price: ${result.price}`);
    } catch (err) {
      console.error('Sell failed:', err);
    }
  };

  const handleModify = async () => {
    try {
      const result = await modify({
        ticket: parseInt(modifyForm.ticket),
        sl: modifyForm.sl ? parseFloat(modifyForm.sl) : undefined,
        tp: modifyForm.tp ? parseFloat(modifyForm.tp) : undefined,
      });
      console.log('Position modified:', result);
      alert(`Position modified! Ticket: ${result.ticket}`);
    } catch (err) {
      console.error('Modify failed:', err);
    }
  };

  const handleClose = async () => {
    try {
      const result = await close({
        ticket: parseInt(closeTicket),
      });
      console.log('Position closed:', result);
      alert(`Position closed! Profit: ${result.profit}`);
    } catch (err) {
      console.error('Close failed:', err);
    }
  };

  return (
    <div className="space-y-4 p-4">
      {/* Connection Status */}
      <Card>
        <CardHeader>
          <CardTitle>Trading Socket Connection</CardTitle>
          <CardDescription>
            Status: {isConnected ?
              <Badge variant="default" className="ml-2">Connected</Badge> :
              <Badge variant="destructive" className="ml-2">Disconnected</Badge>
            }
          </CardDescription>
        </CardHeader>
        <CardContent>
          {accountInfo && (
            <div className="space-y-2">
              <p><strong>Account:</strong> {accountInfo.login}</p>
              <p><strong>Name:</strong> {accountInfo.name}</p>
              <p><strong>Server:</strong> {accountInfo.server}</p>
              <p><strong>Balance:</strong> ${accountInfo.balance.toFixed(2)}</p>
              <p><strong>Equity:</strong> ${accountInfo.equity.toFixed(2)}</p>
              <p><strong>Leverage:</strong> 1:{accountInfo.leverage}</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Error Display */}
      {error && (
        <Alert variant="destructive">
          <AlertDescription>
            {error}
            <Button variant="ghost" size="sm" onClick={clearError} className="ml-2">
              Dismiss
            </Button>
          </AlertDescription>
        </Alert>
      )}

      {/* Login Form */}
      {!isLoggedIn && (
        <Card>
          <CardHeader>
            <CardTitle>Login to MT5</CardTitle>
            <CardDescription>Enter your MT5 account credentials</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="account">Account Number</Label>
              <Input
                id="account"
                type="number"
                placeholder="12345678"
                value={loginForm.account}
                onChange={(e) => setLoginForm({ ...loginForm, account: e.target.value })}
              />
            </div>
            <div>
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                placeholder="Your password"
                value={loginForm.password}
                onChange={(e) => setLoginForm({ ...loginForm, password: e.target.value })}
              />
            </div>
            <div>
              <Label htmlFor="server">Server</Label>
              <Input
                id="server"
                placeholder="Broker-Server"
                value={loginForm.server}
                onChange={(e) => setLoginForm({ ...loginForm, server: e.target.value })}
              />
            </div>
            <Button onClick={handleLogin} disabled={loading || !isConnected}>
              {loading ? 'Logging in...' : 'Login'}
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Trading Operations (shown when logged in) */}
      {isLoggedIn && (
        <>
          {/* Buy/Sell Orders */}
          <Card>
            <CardHeader>
              <CardTitle>Place Order</CardTitle>
              <CardDescription>Execute buy or sell market orders</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="symbol">Symbol</Label>
                  <Input
                    id="symbol"
                    placeholder="EURUSD"
                    value={orderForm.symbol}
                    onChange={(e) => setOrderForm({ ...orderForm, symbol: e.target.value })}
                  />
                </div>
                <div>
                  <Label htmlFor="volume">Volume (lots)</Label>
                  <Input
                    id="volume"
                    type="number"
                    step="0.01"
                    placeholder="0.01"
                    value={orderForm.volume}
                    onChange={(e) => setOrderForm({ ...orderForm, volume: e.target.value })}
                  />
                </div>
                <div>
                  <Label htmlFor="sl">Stop Loss (optional)</Label>
                  <Input
                    id="sl"
                    type="number"
                    step="0.00001"
                    placeholder="1.0950"
                    value={orderForm.sl}
                    onChange={(e) => setOrderForm({ ...orderForm, sl: e.target.value })}
                  />
                </div>
                <div>
                  <Label htmlFor="tp">Take Profit (optional)</Label>
                  <Input
                    id="tp"
                    type="number"
                    step="0.00001"
                    placeholder="1.1050"
                    value={orderForm.tp}
                    onChange={(e) => setOrderForm({ ...orderForm, tp: e.target.value })}
                  />
                </div>
              </div>
              <div className="flex gap-2">
                <Button onClick={handleBuy} disabled={loading} variant="default">
                  {loading ? 'Processing...' : 'Buy'}
                </Button>
                <Button onClick={handleSell} disabled={loading} variant="destructive">
                  {loading ? 'Processing...' : 'Sell'}
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Modify Position */}
          <Card>
            <CardHeader>
              <CardTitle>Modify Position</CardTitle>
              <CardDescription>Update SL/TP for existing position</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <Label htmlFor="modify-ticket">Ticket</Label>
                  <Input
                    id="modify-ticket"
                    type="number"
                    placeholder="123456789"
                    value={modifyForm.ticket}
                    onChange={(e) => setModifyForm({ ...modifyForm, ticket: e.target.value })}
                  />
                </div>
                <div>
                  <Label htmlFor="modify-sl">New SL</Label>
                  <Input
                    id="modify-sl"
                    type="number"
                    step="0.00001"
                    placeholder="1.0960"
                    value={modifyForm.sl}
                    onChange={(e) => setModifyForm({ ...modifyForm, sl: e.target.value })}
                  />
                </div>
                <div>
                  <Label htmlFor="modify-tp">New TP</Label>
                  <Input
                    id="modify-tp"
                    type="number"
                    step="0.00001"
                    placeholder="1.1040"
                    value={modifyForm.tp}
                    onChange={(e) => setModifyForm({ ...modifyForm, tp: e.target.value })}
                  />
                </div>
              </div>
              <Button onClick={handleModify} disabled={loading}>
                {loading ? 'Modifying...' : 'Modify Position'}
              </Button>
            </CardContent>
          </Card>

          {/* Close Position */}
          <Card>
            <CardHeader>
              <CardTitle>Close Position</CardTitle>
              <CardDescription>Close an open position</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label htmlFor="close-ticket">Ticket</Label>
                <Input
                  id="close-ticket"
                  type="number"
                  placeholder="123456789"
                  value={closeTicket}
                  onChange={(e) => setCloseTicket(e.target.value)}
                />
              </div>
              <Button onClick={handleClose} disabled={loading} variant="destructive">
                {loading ? 'Closing...' : 'Close Position'}
              </Button>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
};
